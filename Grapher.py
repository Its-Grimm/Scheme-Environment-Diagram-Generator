import sys
import sexpdata
import graphviz

closure_counter = 0

class Closure:
    """Stores param list, body, and defining environment for a Scheme closure."""
    def __init__(self, params, body, env_id):
        global closure_counter
        self.id = closure_counter
        closure_counter += 1

        self.params = params
        self.body = body
        self.env_id = env_id  # The environment in which this closure was defined

    def __repr__(self):
        # For debug: returns something like <Closure#0 params=(x) env=Env1>
        return f"<Closure#{self.id} params={self.params} env=Env{self.env_id}>"

class Environment:
    """Represents a single environment frame."""
    def __init__(self, env_id, parent=None):
        self.env_id = env_id
        self.parent = parent  # Parent is an Environment or None
        self.bindings = {}    # var -> (value)

    def define(self, var, value):
        self.bindings[var] = value

    def lookup(self, var):
        if var in self.bindings:
            return self.bindings[var]
        elif self.parent:
            return self.parent.lookup(var)
        else:
            raise NameError(f"Unbound variable: {var}")

    def update(self, var, value):
        if var in self.bindings:
            self.bindings[var] = value
        elif self.parent:
            self.parent.update(var, value)
        else:
            raise NameError(f"Unbound variable: {var}")

class SchemeInterpreter:
    def __init__(self):
        self.envs = []       # List of Environment objects
        self.closures = []   # List of Closure objects
        self.graph = graphviz.Digraph(format='dot')

        # Create the global environment (env_id=0)
        global_env = Environment(env_id=0, parent=None)
        self.envs.append(global_env)
        self.global_env = global_env

        # Built-ins
        self._initialize_builtins()

    def _initialize_builtins(self):
        self.global_env.define('+', lambda x, y: x + y)
        self.global_env.define('-', lambda x, y: x - y)
        self.global_env.define('*', lambda x, y: x * y)
        self.global_env.define('/', lambda x, y: x / y)

    def run(self, scheme_code):
        # Parse entire code as a list of top-level expressions
        exprs = sexpdata.loads(f'({scheme_code})')
        for expr in exprs:
            self.eval_expr(expr, self.global_env)
        self.visualize()

    def new_env(self, parent_env):
        """Creates a new Environment with a unique ID and the given parent."""
        env_id = len(self.envs)
        e = Environment(env_id=env_id, parent=parent_env)
        self.envs.append(e)
        return e

    def new_closure(self, params, body, env_id):
        """Creates a new Closure object and stores it in self.closures."""
        c = Closure(params, body, env_id)
        self.closures.append(c)
        return c

    def eval_expr(self, expr, env):
        """Evaluates an expression under a given environment."""
        # 1) Number
        if isinstance(expr, (int, float)):
            return expr

        # 2) Symbol
        if isinstance(expr, sexpdata.Symbol):
            return env.lookup(expr.value())

        # 3) List (S-expression)
        if isinstance(expr, list):
            if not expr:
                return None

            op = expr[0]
            args = expr[1:]

            # (define var expr)
            if op == sexpdata.Symbol('define'):
                var_symbol, val_expr = args
                val = self.eval_expr(val_expr, env)
                env.define(var_symbol.value(), val)
                return val

            # (lambda (params) body...)
            elif op == sexpdata.Symbol('lambda'):
                params = args[0]       # list of parameter symbols
                body_exprs = args[1:]  # one or more body expressions

                # If multiple body expressions, wrap them in (begin ...)
                if len(body_exprs) == 1:
                    body = body_exprs[0]
                else:
                    body = [sexpdata.Symbol('begin')] + body_exprs

                closure_obj = self.new_closure(
                    params=[p.value() for p in params],
                    body=body,
                    env_id=env.env_id  # ID of environment where closure is created
                )
                return closure_obj

            # (begin expr1 expr2 ...)
            elif op == sexpdata.Symbol('begin'):
                result = None
                for subexpr in args:
                    result = self.eval_expr(subexpr, env)
                return result

            # (let ((var val) ...) body...)
            elif op == sexpdata.Symbol('let'):
                binding_list = args[0]
                body_exprs = args[1:]

                # Create a new environment
                let_env = self.new_env(env)
                # Define each var in let_env
                for binding in binding_list:
                    var_sym, val_expr = binding
                    val = self.eval_expr(val_expr, env)
                    let_env.define(var_sym.value(), val)

                # Evaluate body in let_env
                result = None
                for subexpr in body_exprs:
                    result = self.eval_expr(subexpr, let_env)
                return result

            # (set! var expr)
            elif op == sexpdata.Symbol('set!'):
                var_sym, val_expr = args
                val = self.eval_expr(val_expr, env)
                env.update(var_sym.value(), val)
                return val

            # Function call
            else:
                # Evaluate the operator
                proc = self.eval_expr(op, env)

                # If it's a built-in function (callable)
                if callable(proc):
                    evaluated_args = [self.eval_expr(a, env) for a in args]
                    return proc(*evaluated_args)

                # Otherwise, it's a closure
                if isinstance(proc, Closure):
                    # Create a new environment for the function call
                    call_env = self.new_env(self.envs[proc.env_id])
                    # Bind parameters
                    for param, arg_expr in zip(proc.params, args):
                        val = self.eval_expr(arg_expr, env)
                        call_env.define(param, val)

                    # Evaluate closure body in call_env
                    return self.eval_expr(proc.body, call_env)

                raise TypeError(f"Attempted to call non-callable: {proc}")

        # If none of the above matched, return None
        return None

    def visualize(self):
        """Generate a DOT file with separate nodes for frames and closures."""
        # 1) Create nodes for each environment frame
        for env in self.envs:
            label = f"Env{env.env_id}\\n"
            for var, val in env.bindings.items():
                if isinstance(val, Closure):
                    label += f"{var}: Closure#{val.id}\\n"
                else:
                    label += f"{var}: {val}\\n"
            self.graph.node(
                f"env_{env.env_id}",
                label=label,
                shape="box",
                style="filled",
                fillcolor="lightyellow"
            )

            # Draw edge from env to its parent
            if env.parent:
                self.graph.edge(f"env_{env.parent.env_id}", f"env_{env.env_id}")

        # 2) Create nodes for closures
        for c in self.closures:
            label = (
                f"Closure#{c.id}\\n"
                f"params: {c.params}\\n"
                f"body: {self._format_body(c.body)}\\n"
                f"def-env: Env{c.env_id}"
            )
            self.graph.node(
                f"closure_{c.id}",
                label=label,
                shape="box",
                style="rounded, filled",
                fillcolor="lightblue"
            )
            # Arrow from closure -> environment where it was defined
            self.graph.edge(f"closure_{c.id}", f"env_{c.env_id}", label="parent-env")

        # 3) Draw edges from environment frames to closures for variables referencing them
        for env in self.envs:
            for var, val in env.bindings.items():
                if isinstance(val, Closure):
                    self.graph.edge(f"env_{env.env_id}", f"closure_{val.id}", label=var)

        # Save final dot
        with open("env_diagram.dot", "w") as f:
            f.write(self.graph.source)
        print("Environment diagram saved as env_diagram.dot.")
        print("Use 'dot -Tpng env_diagram.dot -o env_diagram.png' to render it.")

    def _format_body(self, body):
        """Small helper to make the closure body more readable in the label."""
        if isinstance(body, list):
            # Convert S-expressions to string
            return " ".join(str(x) for x in body)
        return str(body)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r") as f:
            code = f.read()
    else:
        print("Enter your Scheme code (end with Ctrl-D):")
        code = sys.stdin.read()

    interp = SchemeInterpreter()
    interp.run(code)
