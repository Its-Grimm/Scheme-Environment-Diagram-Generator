import sexpdata  # Parses Scheme S-expressions
import graphviz  # For visualization

class Environment:
    """Represents an environment frame with variable bindings."""
    def __init__(self, parent=None):
        self.bindings = {}
        self.parent = parent  # Link to parent environment

    def define(self, var, value):
        self.bindings[var] = value

    def lookup(self, var):
        if var in self.bindings:
            return self.bindings[var]
        elif self.parent:
            return self.parent.lookup(var)
        else:
            raise NameError(f"Unbound variable: {var}")

class SchemeInterpreter:
    """Processes Scheme code to build an environment model."""
    def __init__(self):
        self.global_env = Environment()
        self.frames = [self.global_env]  # Include global environment in frames
        self.graph = graphviz.Digraph(format='png')  # Graph for visualization
        self._initialize_builtins()

    def _initialize_builtins(self):
        """Defines built-in operators in the global environment."""
        self.global_env.define('+', lambda x, y: x + y)
        self.global_env.define('-', lambda x, y: x - y)
        self.global_env.define('*', lambda x, y: x * y)
        self.global_env.define('/', lambda x, y: x / y)

    def eval_expr(self, expr, env):
        """Evaluates an expression and tracks variable bindings."""
        if isinstance(expr, (int, float)):
            return expr  # Numbers evaluate to themselves
        
        if isinstance(expr, sexpdata.Symbol):
            return env.lookup(expr.value())  # Lookup variable value
        
        if isinstance(expr, list):
            if not expr:
                return None
            op = expr[0]
            args = expr[1:]
            
            if op == sexpdata.Symbol('define'):  # Variable definition
                var, value_expr = args
                value = self.eval_expr(value_expr, env)
                env.define(var.value(), value)
                return value
            
            elif op == sexpdata.Symbol('lambda'):  # Function definition
                params, body = args
                closure = ([p.value() for p in params], body, env)  # Store function environment
                return closure
            
            else:  # Function call
                procedure = self.eval_expr(op, env)
                if callable(procedure):  # Built-in function
                    evaluated_args = [self.eval_expr(arg, env) for arg in args]
                    return procedure(*evaluated_args)
                
                params, body, closure_env = procedure
                new_env = Environment(parent=closure_env)
                self.frames.append(new_env)  # Track environment creation
                
                for param, arg in zip(params, args):
                    new_env.define(param, self.eval_expr(arg, env))
                
                return self.eval_expr(body, new_env)

    def visualize(self):
        """Creates an environment diagram."""
        for i, frame in enumerate(self.frames):
            label = f"Frame {i}\n" + "\n".join(f"{k}: {v}" for k, v in frame.bindings.items())
            self.graph.node(str(i), label=label, shape='box')
            if frame.parent and frame.parent in self.frames:
                parent_idx = self.frames.index(frame.parent)
                self.graph.edge(str(parent_idx), str(i))
        try:
            display(self.graph)  # Display graph in Jupyter/IPython environment
        except NameError:
            print("Graph visualization is not supported in this environment.")

    def run(self, scheme_code):
        """Parses and executes a Scheme program."""
        exprs = sexpdata.loads(f'({scheme_code})')  # Wrap input in parentheses to ensure valid structure
        for expr in exprs:
            self.eval_expr(expr, self.global_env)
        self.visualize()

# Example Scheme program
scheme_code = """
(define square (lambda (x) (* x x)))
(define result (square 5))
"""

interpreter = SchemeInterpreter()
interpreter.run(scheme_code)
