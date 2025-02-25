import sys
import sexpdata
import graphviz

# We keep a global counter so each closure has a unique ID.
closure_counter = 0

class Closure:
    """Represents a Scheme closure with parameters, body, and its defining environment."""
    def __init__(self, params, body, def_env_id):
        global closure_counter
        self.id = closure_counter
        closure_counter += 1
        self.params = params            # list of parameter names
        self.body = body               # the body s-expression (could be (begin ...) if multiple exprs)
        self.def_env_id = def_env_id   # environment ID in which this closure was defined

    def __repr__(self):
        return f"<Closure#{self.id} params={self.params} def_env=Frame {self.def_env_id}>"

class Environment:
    """Represents a single environment frame."""
    def __init__(self, env_id, parent=None):
        self.env_id = env_id          # Unique integer ID
        self.parent = parent          # Another Environment or None
        self.bindings = {}            # var -> value (which might be a number, a closure, etc.)

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
    """A simplified Scheme interpreter that tracks environment frames for diagramming."""
    def __init__(self):
        self.envs = []       # list of Environment objects
        self.closures = []   # list of Closure objects
        self.graph = graphviz.Digraph(format='dot')

        # Create the global environment (Frame 0).
        global_env = Environment(env_id=0, parent=None)
        self.envs.append(global_env)
        self.global_env = global_env

        self._initialize_builtins()

    def _initialize_builtins(self):
        # Basic arithmetic
        self.global_env.define('+', lambda x, y: x + y)
        self.global_env.define('-', lambda x, y: x - y)
        self.global_env.define('*', lambda x, y: x * y)
        self.global_env.define('/', lambda x, y: x / y)

    def new_env(self, parent_env):
        """Create a new Environment with a unique ID, child of parent_env."""
        env_id = len(self.envs)
        e = Environment(env_id=env_id, parent=parent_env)
        self.envs.append(e)
        return e

    def new_closure(self, params, body, def_env_id):
        """Create a new Closure object and store it."""
        c = Closure(params, body, def_env_id)
        self.closures.append(c)
        return c

    def run(self, scheme_code):
        """Parse and evaluate the entire Scheme program, then visualize."""
        exprs = sexpdata.loads(f'({scheme_code})')  # read as a list of top-level forms
        for expr in exprs:
            self.eval_expr(expr, self.global_env)
        self.visualize()

    def eval_expr(self, expr, env):
        """Evaluate a Scheme expression in a given environment."""
        # 1) Numeric literals
        if isinstance(expr, (int, float)):
            return expr

        # 2) Symbols
        if isinstance(expr, sexpdata.Symbol):
            return env.lookup(expr.value())

        # 3) S-expressions
        if isinstance(expr, list):
            if not expr:
                return None
            op = expr[0]
            args = expr[1:]

            # (define var expr)
            if op == sexpdata.Symbol('define'):
                var_sym, val_expr = args
                val = self.eval_expr(val_expr, env)
                env.define(var_sym.value(), val)
                return val

            # (lambda (params) body...)
            elif op == sexpdata.Symbol('lambda'):
                params = args[0]
                body_exprs = args[1:]
                # If multiple expressions, wrap them in (begin ...)
                if len(body_exprs) == 1:
                    body = body_exprs[0]
                else:
                    body = [sexpdata.Symbol('begin')] + body_exprs

                closure_obj = self.new_closure(
                    params=[p.value() for p in params],
                    body=body,
                    def_env_id=env.env_id
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
                let_env = self.new_env(env)
                # bind each var
                for binding in binding_list:
                    var_sym, val_expr = binding
                    val = self.eval_expr(val_expr, env)
                    let_env.define(var_sym.value(), val)
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
                proc = self.eval_expr(op, env)
                if callable(proc):
                    # Built-in function
                    evaluated_args = [self.eval_expr(a, env) for a in args]
                    return proc(*evaluated_args)
                elif isinstance(proc, Closure):
                    # Evaluate closure
                    call_env = self.new_env(self.envs[proc.def_env_id])
                    # bind parameters
                    for param, arg_expr in zip(proc.params, args):
                        val = self.eval_expr(arg_expr, env)
                        call_env.define(param, val)
                    return self.eval_expr(proc.body, call_env)
                else:
                    raise TypeError(f"Attempted to call non-callable: {proc}")

        return None

    def visualize(self):
        """
        Produce a DOT file that draws environment frames as rectangles
        and closures as TWO red circles: one for 'args', one for 'body',
        with arrows matching CS61A's style.
        """
        # 1) Draw each environment as a rectangle with variable labels.
        for env in self.envs:
            if env.env_id == 0:
                label = "Global Environment\\n"
            else:
                label = f"Frame {env.env_id}\\n"

            # We'll just list the variables (the actual pointer to closures
            # is an arrow drawn below).
            for var, val in env.bindings.items():
                if isinstance(val, Closure):
                    label += f"{var} -> Closure#{val.id}\\n"
                else:
                    label += f"{var} = {val}\\n"

            self.graph.node(
                f"env_{env.env_id}",
                label=label,
                shape="box",
                style="filled",
                fillcolor="#FFF2B6"  # pale yellow
            )

            # Edge from env to its parent
            if env.parent:
                self.graph.edge(
                    f"env_{env.parent.env_id}",
                    f"env_{env.env_id}",
                    label="parent",
                    style="dotted"
                )

        # 2) For each closure, create a subgraph with two red circles:
        #    closure_X_args and closure_X_body, connected by an edge.
        #    We'll also draw an arrow from the 'body' circle to the
        #    environment in which it was defined.
        for clos in self.closures:
            sub = graphviz.Digraph(name=f"cluster_closure_{clos.id}")
            sub.attr(color="none")  # no border on subgraph

            # Circle for 'args'
            args_node_name = f"closure_{clos.id}_args"
            sub.node(
                args_node_name,
                label=f"args: ({' '.join(clos.params)})",
                shape="circle",
                style="filled",
                fillcolor="#ff9999",  # light red
                color="red"
            )

            # Circle for 'body'
            body_node_name = f"closure_{clos.id}_body"
            # We can format the body for readability
            body_str = self._format_expr(clos.body)
            sub.node(
                body_node_name,
                label=f"body: {body_str}",
                shape="circle",
                style="filled",
                fillcolor="#ff9999",
                color="red"
            )

            # Connect the two circles
            sub.edge(args_node_name, body_node_name, color="red")

            # Add this subgraph to the main graph
            self.graph.subgraph(sub)

            # Arrow from the body circle to the environment where it was defined
            self.graph.edge(
                body_node_name,
                f"env_{clos.def_env_id}",
                label="def-env",
                style="dashed",
                color="red"
            )

        # 3) Draw edges from environment frames to each closure's 'args' circle,
        #    for variables referencing that closure.
        for env in self.envs:
            for var, val in env.bindings.items():
                if isinstance(val, Closure):
                    # Link env -> closure_X_args
                    self.graph.edge(
                        f"env_{env.env_id}",
                        f"closure_{val.id}_args",
                        label=var,
                        color="blue"
                    )

        # Finally, write out the DOT file
        with open("env_diagram.dot", "w") as f:
            f.write(self.graph.source)

        print("Environment diagram saved as env_diagram.dot.")
        print("Use 'dot -Tpng env_diagram.dot -o env_diagram.png' to render it.")

    def _format_expr(self, expr):
        """Convert an S-expression into a string for labeling."""
        if isinstance(expr, list):
            return "(" + " ".join(self._format_expr(e) for e in expr) + ")"
        elif isinstance(expr, sexpdata.Symbol):
            return expr.value()
        return str(expr)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r") as file:
            scheme_code = file.read()
    else:
        print("Enter your Scheme code (end with Ctrl-D):")
        scheme_code = sys.stdin.read()

    interp = SchemeInterpreter()
    interp.run(scheme_code)
