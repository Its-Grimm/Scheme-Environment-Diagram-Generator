import sys
import sexpdata
import graphviz

closure_counter = 0

class Closure:
    """Represents a Scheme closure with parameters, body, and the environment ID where it was defined."""
    def __init__(self, params, body, def_env_id):
        global closure_counter
        self.id = closure_counter
        closure_counter += 1

        self.params = params
        self.body = body
        self.def_env_id = def_env_id

    def __repr__(self):
        return f"<Closure#{self.id} params={self.params} def_env=E{self.def_env_id}>"

class Environment:
    """Represents an environment frame."""
    def __init__(self, env_id, parent=None, is_global=False):
        self.env_id = env_id
        self.parent = parent
        self.is_global = is_global
        self.bindings = {}  # var -> value (int, float, or Closure)

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
    """Generates an environment diagram in a style similar to CS61AS, with two red circles for each procedure."""
    def __init__(self):
        self.envs = []
        self.closures = []
        self.graph = graphviz.Digraph(format='dot')

        # Create global environment (ID=0)
        global_env = Environment(env_id=0, parent=None, is_global=True)
        self.envs.append(global_env)
        self.global_env = global_env

        self._initialize_builtins()

    def _initialize_builtins(self):
        # Built-ins won't be displayed individually, but we mention "[other bindings]" in Global
        self.global_env.define('+', lambda x, y: x + y)
        self.global_env.define('-', lambda x, y: x - y)
        self.global_env.define('*', lambda x, y: x * y)
        self.global_env.define('/', lambda x, y: x / y)

    def new_env(self, parent_env):
        env_id = len(self.envs)
        e = Environment(env_id=env_id, parent=parent_env, is_global=False)
        self.envs.append(e)
        return e

    def new_closure(self, params, body, def_env_id):
        c = Closure(params, body, def_env_id)
        self.closures.append(c)
        return c

    def run(self, scheme_code):
        # Parse top-level expressions
        exprs = sexpdata.loads(f'({scheme_code})')
        for expr in exprs:
            self.eval_expr(expr, self.global_env)
        self.visualize()

    def eval_expr(self, expr, env):
        # 1) Numbers
        if isinstance(expr, (int, float)):
            return expr
        # 2) Symbol
        if isinstance(expr, sexpdata.Symbol):
            return env.lookup(expr.value())
        # 3) S-expression
        if isinstance(expr, list) and expr:
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
                if len(body_exprs) == 1:
                    body = body_exprs[0]
                else:
                    body = [sexpdata.Symbol('begin')] + body_exprs
                return self.new_closure(
                    params=[p.value() for p in params],
                    body=body,
                    def_env_id=env.env_id
                )

            # (begin expr1 expr2 ...)
            elif op == sexpdata.Symbol('begin'):
                result = None
                for subexpr in args:
                    result = self.eval_expr(subexpr, env)
                return result

            # (let ((v e) ...) body...)
            elif op == sexpdata.Symbol('let'):
                binding_list = args[0]
                body_exprs = args[1:]
                let_env = self.new_env(env)
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
                    # Built-in
                    evaluated_args = [self.eval_expr(a, env) for a in args]
                    return proc(*evaluated_args)
                elif isinstance(proc, Closure):
                    call_env = self.new_env(self.envs[proc.def_env_id])
                    for param, arg_expr in zip(proc.params, args):
                        val = self.eval_expr(arg_expr, env)
                        call_env.define(param, val)
                    return self.eval_expr(proc.body, call_env)
                else:
                    raise TypeError(f"Attempted to call non-callable: {proc}")

        return None

    def visualize(self):
        """Create a DOT file with environment frames and side-by-side red circles for closures."""
        # 1) Draw environment frames
        for env in self.envs:
            if env.is_global:
                # Global environment label
                label = "Global Environment\\n[other bindings]\\n"
            else:
                # Non-global: E1, E2, etc.
                label = f"E{env.env_id}\\n"

            # Show user-defined variables
            for var, val in env.bindings.items():
                # Skip built-ins in global
                if env.is_global and callable(val) and val.__name__ == '<lambda>':
                    continue
                if isinstance(val, (int, float)):
                    label += f"{var} -> {val}\\n"
                elif isinstance(val, Closure):
                    # We'll draw an arrow from env to the closure's left circle
                    label += f"{var}\\n"
                else:
                    label += f"{var} -> {val}\\n"

            self.graph.node(
                f"env_{env.env_id}",
                label=label,
                shape="box",
                style="filled",
                fillcolor="#FFFFCC"
            )

            # Parent link (solid line)
            if env.parent is not None:
                self.graph.edge(
                    f"env_{env.parent.env_id}",
                    f"env_{env.env_id}",
                    color="black"
                )

        # 2) Draw closures: two red circles side-by-side
        for clos in self.closures:
            # We'll put them in a subgraph with rankdir=LR so they're side by side
            sub = graphviz.Digraph(name=f"cluster_closure_{clos.id}")
            sub.attr(rankdir='LR', color='none')

            left_id = f"closure_{clos.id}_left"
            right_id = f"closure_{clos.id}_right"

            # Two small red circles, side by side
            sub.node(
                left_id,
                label="",
                shape="circle",
                style="filled",
                fillcolor="red",
                color="red",
                fixedsize="true",
                width="0.3",
                height="0.3"
            )
            sub.node(
                right_id,
                label="",
                shape="circle",
                style="filled",
                fillcolor="red",
                color="red",
                fixedsize="true",
                width="0.3",
                height="0.3"
            )

            # Connect them with an invisible edge so they “touch”
            sub.edge(left_id, right_id, style="invis")

            # Now create shape=none nodes for args and body, each attached to the left circle
            args_node = f"closure_{clos.id}_args"
            body_node = f"closure_{clos.id}_body"

            # For labeling
            args_label = f"args: ({' '.join(clos.params)})"
            body_label = f"body: {self._format_expr(clos.body)}"

            sub.node(args_node, label=args_label, shape="none")
            sub.node(body_node, label=body_label, shape="none")

            # Red arrow from left circle to args
            sub.edge(left_id, args_node, color="red", arrowhead="normal")
            # Red arrow from left circle to body
            sub.edge(left_id, body_node, color="red", arrowhead="normal")

            # Add subgraph to main
            self.graph.subgraph(sub)

            # Solid red line from right circle to environment
            self.graph.edge(
                right_id,
                f"env_{clos.def_env_id}",
                color="red"
            )

        # 3) For each closure binding, a red arrow from environment to left circle
        for env in self.envs:
            for var, val in env.bindings.items():
                if isinstance(val, Closure):
                    left_circle = f"closure_{val.id}_left"
                    self.graph.edge(
                        f"env_{env.env_id}",
                        left_circle,
                        label=var,
                        color="red"
                    )

        # Output DOT
        with open("env_diagram.dot", "w") as f:
            f.write(self.graph.source)
        print("Environment diagram saved as env_diagram.dot.")
        print("Use 'dot -Tpng env_diagram.dot -o env_diagram.png' to render it.")

    def _format_expr(self, expr):
        """Convert an S-expression to a string."""
        if isinstance(expr, list):
            return "(" + " ".join(self._format_expr(e) for e in expr) + ")"
        elif isinstance(expr, sexpdata.Symbol):
            return expr.value()
        return str(expr)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r") as file:
            code = file.read()
    else:
        print("Enter your Scheme code (end with Ctrl-D):")
        code = sys.stdin.read()

    interp = SchemeInterpreter()
    interp.run(code)
