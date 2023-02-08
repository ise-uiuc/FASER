from src.lib.AssertSpec import AssertSpec
import ast
import shutil
import astunparse
import os
from ast import *

# ast nodes
from src.lib.AssertType import AssertType

numpy_import = ast.Import(names=[ast.alias(name='numpy', asname='np')])
torch_import = ast.Import(names=[ast.alias(name='torch', asname=None)])
pytest_import = ast.Import(names=[ast.alias(name='pytest', asname=None)])
tensorflow_import = ast.Import(
    names=[ast.alias(name='tensorflow', asname='tf')])
random_import = ast.Import(names=[ast.alias(name='random', asname=None)])
sys_import = ast.Import(names=[ast.alias(name='sys', asname=None)])

string_formatter = '''
def sample_to_string(mystr):
    if isinstance(mystr, list):
        return "[{0}]".format(','.join([sample_to_string(i) for i in mystr]))
    if isinstance(mystr, np.ndarray):
        return np.array2string(mystr, max_line_width=np.inf, precision=100, separator=',', threshold=np.inf).replace('\\n', '')
    try:
        if isinstance(mystr, torch.Tensor):
            return np.array2string(mystr.detach().numpy(), max_line_width=np.inf, precision=100, separator=',',
                                   threshold=np.inf).replace('\\n', '')
    except:
        pass
    try:
        if isinstance(mystr, tf.Tensor):
            with tf.Session():
                return np.array2string(mystr.eval(), max_line_width=np.inf, precision=100, separator=',', threshold=np.inf).replace(
                    '\\n', '')
    except:
        pass
    try:
        return np.array2string(np.asanyarray(mystr), max_line_width=np.inf, precision=100, separator=',', threshold=np.inf).replace('\\n', '')
    except:
        pass
    return str(mystr)
    '''


class TestInstrumentor(ast.NodeTransformer):

    def __init__(self, assert_spec: AssertSpec, logstring: str, deps: list):
        self.assert_spec = assert_spec

        if self.assert_spec.base_assert is not None:
            self.assert_spec_base = self.assert_spec.base_assert
        else:
            self.assert_spec_base = None
        self.flag_visit = False
        self.assert_strings = ['assertGreater', 'assert_almost_equal', 'assert_approx_equal',
                               'assert_array_almost_equal',
                               'assertLess', 'assertGreaterEqual', "assertLessEqual", 'assert', 'assert_equal',
                               'assertTrue', 'assertFalse', 'assertEqual', 'assert_almost_equal', 'assert_allclose',
                               'assert_array_less']
        self.log_string = logstring
        self.modified_ast = None
        self.modified_ast_base = None
        self.func_col_offset = 0
        self.dependencies = deps
        self.add_print = True
        self.val = 1

    def _generate_seed_stub(self, varname, lib_alias, lib_func, seed_size):
        return [
            Assign(targets=[Name(id=varname, ctx=Store())], value=Call(
                func=Attribute(value=Attribute(value=Name(id='np', ctx=Load()), attr='random', ctx=Load()),
                               attr='randint',
                               ctx=Load()), args=[Attribute(
                                   value=Call(func=Attribute(value=Name(id='np', ctx=Load()), attr='iinfo', ctx=Load()),
                                              args=[Attribute(value=Name(
                                                  id='np', ctx=Load()), attr=seed_size, ctx=Load())],
                                              keywords=[]),
                                   attr='max', ctx=Load())], keywords=[])),
            Expr(value=Call(
                func=Attribute(value=Name(id=lib_alias, ctx=Load()),
                               attr=lib_func, ctx=Load()),
                args=[Name(id=varname, ctx=Load())], keywords=[])),
            Expr(
                value=Call(func=Name(id='print', ctx=Load()),
                           args=[BinOp(left=Str(s='\n{0} seed: %s'.format(lib_alias)),
                                       op=Mod(),
                                       right=Name(id=varname, ctx=Load()))],
                           keywords=[]))

        ]

    def _create_string_formatter(self):
        string_formatter_nodes = ast.parse(string_formatter)
        return string_formatter_nodes.body[0]

    def _create_fixture(self):
        body = []
        if 'numpy' in self.dependencies:
            body = body + \
                self._generate_seed_stub(
                    'npseed', 'np.random', 'seed', 'int32')
        if 'torch' in self.dependencies:
            body = body + \
                self._generate_seed_stub(
                    'torchseed', 'torch', 'manual_seed', 'int64')
        if 'tensorflow' in self.dependencies:
            trypart = self._generate_seed_stub(
                'tfseed', 'tf', 'set_random_seed', 'int64')
            exceptpart = self._generate_seed_stub(
                'tfseed', 'tf.random', 'set_seed', 'int64')
            body = body + [Try(body=trypart, orelse=[], finalbody=[], handlers=[
                ast.ExceptHandler(type=Name(id='Exception', ctx=Load()), name=None, body=exceptpart)])]
        if 'random' in self.dependencies:
            body = body + self._generate_seed_stub('randseed', 'random', 'seed', 'int32')
        fixture_func = ast.FunctionDef(
            name='show_guts',
            args=ast.arguments(
                args=[],
                vararg=None,
                kwonlyargs=[],
                kw_defaults=[],
                kwarg=None,
                defaults=[]),
            body=body,
            decorator_list=[
                Call(func=Attribute(value=Name(id='pytest', ctx=Load()), attr='fixture', ctx=Load()), args=[],
                     keywords=[keyword(arg='scope', value=Str(s='session'))])],
            returns=None)

        return fixture_func

    def instrument(self):
        # instrument base class if present: imports, print, sample_to_str (only if different file)
        if self.assert_spec_base is not None and self.assert_spec_base.test.filename != self.assert_spec.test.filename:
            with open(self.assert_spec_base.test.filename, encoding='utf-8') as file:
                fileast = ast.parse(file.read())
                self.add_print = True
                modified = self.visit(fileast)
                self.add_print = False
                modified = ast.fix_missing_locations(modified)
                str_formatter = self._create_string_formatter()
                pos = [i for i in range(len(modified.body)) if isinstance(
                    modified.body[i], ast.ClassDef)]
                if len(pos) == 0:
                    pos = [0]
                pos = pos[0]
                modified.body.insert(pos, str_formatter)
                modified.body.insert(pos, pytest_import)
                modified.body.insert(pos, sys_import)
                if 'numpy' in self.dependencies:
                    modified.body.insert(pos, numpy_import)
                if 'torch' in self.dependencies:
                    modified.body.insert(pos, torch_import)
                if 'tensorflow' in self.dependencies:
                    modified.body.insert(pos, tensorflow_import)
                if 'random' in self.dependencies:
                    modified.body.insert(pos, random_import)
                self.modified_ast_base = modified
        else:
            # instrument child class or the main class (if no base class)
            with open(self.assert_spec.test.filename, encoding='utf-8') as file:
                fileast = ast.parse(file.read())

                modified = self.visit(fileast)
                modified = ast.fix_missing_locations(modified)
                fixture_func = self._create_fixture()

                # find position of class def.. insert before first class def
                pos = [i for i in range(len(modified.body)) if isinstance(
                    modified.body[i], ast.ClassDef)]
                if len(pos) == 0:
                    pos = [0]
                pos = pos[0]
                # allow only if either no base class or base class in same file
                if self.assert_spec_base is None or self.assert_spec_base.test.filename == self.assert_spec.test.filename:
                    str_formatter = self._create_string_formatter()
                    modified.body.insert(pos, str_formatter)
                modified.body.insert(pos, fixture_func)
                modified.body.insert(pos, pytest_import)
                modified.body.insert(pos, sys_import)
                if 'numpy' in self.dependencies:
                    modified.body.insert(pos, numpy_import)
                if 'torch' in self.dependencies:
                    modified.body.insert(pos, torch_import)
                if 'tensorflow' in self.dependencies:
                    modified.body.insert(pos, tensorflow_import)
                if 'random' in self.dependencies:
                    modified.body.insert(pos, random_import)
                self.modified_ast = modified

    def write_file(self):
        # backup original file
        shutil.copy(self.assert_spec.test.filename,
                    self.assert_spec.test.filename + ".bak")

        # write new file
        with open(self.assert_spec.test.filename, 'w', encoding='utf-8') as file:
            file.write(astunparse.unparse(self.modified_ast).strip())

        if self.modified_ast_base is not None:
            shutil.copy(self.assert_spec_base.test.filename,
                        self.assert_spec_base.test.filename + ".bak")
            with open(self.assert_spec_base.test.filename, 'w', encoding='utf-8') as file:
                file.write(astunparse.unparse(self.modified_ast_base).strip())

    def restore_file(self, savedir=None):
        # save a copy of the file
        if savedir is not None:
            shutil.move(self.assert_spec.test.filename,
                        os.path.join(savedir, self.assert_spec.test.filename.split("/")[-1]))
            if self.modified_ast_base is not None:
                shutil.move(self.assert_spec_base.test.filename,
                            os.path.join(savedir, self.assert_spec_base.test.filename.split("/")[-1]))

        # restore original file
        shutil.move(self.assert_spec.test.filename +
                    ".bak", self.assert_spec.test.filename)
        if self.modified_ast_base is not None:
            shutil.move(self.assert_spec_base.test.filename +
                        ".bak", self.assert_spec_base.test.filename)

    def get_print_stmt(self, node):
        repl_node = Assign(targets=[Name(id='val_{0}'.format(self.val), ctx=Store())],
                           value=node)
        if "pytorch-deps\garage" in self.assert_spec.test.filename:
            print_node = ast.parse(
                "sys.stderr.write(('{0}%s\n' % sample_to_string({1}) ))".format(self.log_string,
                                                                                'val_{0}'.format(self.val)))
        else:
            print_node = ast.parse(
                "print(('{0}%s' % sample_to_string({1}) ))".format(self.log_string,
                                                                   'val_{0}'.format(self.val)))
        self.val += 1
        return [repl_node, print_node]

        mainnode = If(test=Call(func=Name(id='isinstance', ctx=Load()), args=[repl_node.targets[0], Attribute(
            value=Name(id='np', ctx=Load()), attr='ndarray', ctx=Load())], keywords=[]),
            body=[Assign(targets=[Name(id='log_str', ctx=Store())],
                         value=Call(func=Attribute(value=Call(
                             func=Attribute(value=Name(
                                 id='np', ctx=Load()), attr='array2string', ctx=Load()),
                             args=[repl_node.targets[0]], keywords=[keyword(arg='max_line_width',
                                                                            value=Attribute(
                                                                                value=Name(id='np',
                                                                                           ctx=Load()),
                                                                                attr='inf',
                                                                                ctx=Load())),
                                                                    keyword(arg='separator',
                                                                            value=Str(s=',')),
                                                                    keyword(arg='threshold',
                                                                            value=Attribute(
                                                                                value=Name(
                                                                                    id='np',
                                                                                    ctx=Load()),
                                                                                attr='inf',
                                                                                ctx=Load()))]),
                             attr='replace', ctx=Load()), args=[Str(s='\n'), Str(s='')],
                keywords=[])),
            Expr(value=Call(func=Name(id='print', ctx=Load()),
                            args=[BinOp(left=Str(s=self.log_string + '%s'), op=Mod(),
                                        right=Name(id='log_str', ctx=Load()))],
                            keywords=[]))],
            orelse=[])
        lastelse = mainnode.orelse
        if 'tensorflow' in self.dependencies:
            lastelse.append(
                If(test=Call(func=Name(id='isinstance', ctx=Load()), args=[repl_node.targets[0],
                                                                           Attribute(value=Name(id='tf', ctx=Load()),
                                                                                     attr='Tensor', ctx=Load())],
                             keywords=[]), body=[With(items=[withitem(
                                 context_expr=Call(func=Attribute(value=Name(id='tf', ctx=Load()), attr='Session', ctx=Load()),
                                                   args=[], keywords=[]), optional_vars=None)], body=[
                                 Assign(targets=[Name(id='log_str', ctx=Store())],
                                        value=Call(func=Attribute(value=Call(
                                            func=Attribute(value=Name(
                                                id='np', ctx=Load()), attr='array2string', ctx=Load()),
                                            args=[Call(
                                                func=Attribute(
                                                    value=repl_node.targets[0], attr='eval', ctx=Load()),
                                                args=[], keywords=[])], keywords=[keyword(arg='max_line_width',
                                                                                          value=Attribute(
                                                                                              value=Name(
                                                                                                  id='np', ctx=Load()),
                                                                                              attr='inf', ctx=Load())),
                                                                                  keyword(
                                                    arg='separator', value=Str(s=',')),
                                                keyword(arg='threshold', value=Attribute(
                                                    value=Name(
                                                        id='np', ctx=Load()),
                                                    attr='inf', ctx=Load()))]),
                                            attr='replace', ctx=Load()), args=[Str(s='\n'), Str(s='')],
                                     keywords=[])),
                                 Expr(
                                     value=Call(func=Name(id='print', ctx=Load()),
                                                args=[BinOp(left=Str(s='log>>>%s'), op=Mod(
                                                ), right=Name(id='log_str', ctx=Load()))],
                                                keywords=[]))])], orelse=[])
            )
            lastelse = lastelse[0].orelse

        if 'torch' in self.dependencies:
            lastelse.append(If(test=Call(func=Name(id='isinstance', ctx=Load()), args=[repl_node.targets[0],
                                                                                       Attribute(value=Name(id='torch',
                                                                                                            ctx=Load()),
                                                                                                 attr='Tensor',
                                                                                                 ctx=Load())],
                                         keywords=[]),
                               body=[Assign(targets=[Name(id='log_str', ctx=Store())], value=Call(
                                   func=Attribute(value=Call(
                                       func=Attribute(value=Name(
                                           id='np', ctx=Load()), attr='array2string', ctx=Load()),
                                       args=[
                                           Call(func=Attribute(value=repl_node.targets[0], attr='detach().numpy',
                                                               ctx=Load()), args=[],
                                                keywords=[])], keywords=[keyword(arg='max_line_width',
                                                                                 value=Attribute(
                                                                                     value=Name(
                                                                                         id='np', ctx=Load()),
                                                                                     attr='inf',
                                                                                     ctx=Load())),
                                                                         keyword(
                                                                             arg='separator', value=Str(s=',')),
                                                                         keyword(arg='threshold',
                                                                                 value=Attribute(
                                                                                     value=Name(
                                                                                         id='np',
                                                                                         ctx=Load()),
                                                                                     attr='inf',
                                                                                     ctx=Load()))]),
                                       attr='replace', ctx=Load()), args=[Str(s='\n'), Str(s='')],
                                   keywords=[])),
                Expr(value=Call(func=Name(id='print', ctx=Load()), args=[
                    BinOp(left=Str(s='log>>>%s'), op=Mod(),
                          right=Name(id='log_str', ctx=Load()))], keywords=[]))], orelse=[]))
            lastelse = lastelse[0].orelse

        lastelse.append(
            Expr(value=Call(func=Name(id='print', ctx=Load()),
                            args=[BinOp(left=Str(s='log>>>%s'),
                                        op=Mod(), right=repl_node.targets[0])],
                            keywords=[]))
        )

        return [repl_node, mainnode]

    def visit(self, node):
        # lineno = node.lineno  # self.get_lineno(node) + 1

        if isinstance(node, ast.FunctionDef):
            if node.name == self.assert_spec.test.testname:
                node.decorator_list.append(ast.Call(
                    func=ast.Attribute(
                        value=ast.Attribute(
                            value=ast.Name(
                                id='pytest',
                                ctx=ast.Load()),
                            attr='mark',
                            ctx=ast.Load()),
                        attr='usefixtures',
                        ctx=ast.Load()),
                    args=[ast.Str(s='show_guts')],
                    keywords=[]))
                self.flag_visit = True
                self.func_col_offset = node.col_offset
            else:
                # this is to safeguard against internal functions
                if node.col_offset < self.func_col_offset:
                    self.flag_visit = False

        if self.flag_visit and isinstance(node,
                                          ast.stmt) and 0 <= node.col_offset < self.func_col_offset:
            self.flag_visit = False

        if not self.add_print:
            self.generic_visit(node)
            return node

        if isinstance(node, ast.Expr):
            if isinstance(node.value, ast.Call):
                if isinstance(node.value.func, ast.Name):
                    if node.lineno != self.assert_spec.line and self.assert_spec.line != -1:
                        return node
                    stmt = []
                    if AssertType.get_assert_type(node.value.func.id) is not None:
                        # asserts with compare exp inside
                        if node.value.func.id in ['assertTrue', 'assertFalse'] and isinstance(node.value.args[0],
                                                                                              ast.Compare):
                            printstmt = self.get_print_stmt(
                                node.value.args[0].left)
                            node.value.args[0].left = printstmt[0].targets[0]
                            stmt.extend(printstmt)
                            for i, c in enumerate(node.value.args[0].comparators):
                                printstmt2 = self.get_print_stmt(c)
                                stmt.extend(printstmt2)
                                node.value.args[0].comparators[i] = printstmt2[0].targets[0]
                        else:
                            # asserts without compare exp inside
                            for i, c in enumerate(node.value.args):
                                if i < 2:
                                    printstmt = self.get_print_stmt(c)
                                    stmt.extend(printstmt)
                                    node.value.args[i] = printstmt[0].targets[0]
                    stmt.append(node)
                    return stmt
                elif isinstance(node.value.func, ast.Attribute):
                    if node.lineno != self.assert_spec.line and self.assert_spec.line != -1:
                        return node
                    stmt = []
                    if AssertType.get_assert_type(node.value.func.attr) is not None:
                        if node.value.func.attr in ['assertTrue', 'assertFalse'] and isinstance(node.value.args[0],
                                                                                                ast.Compare):
                            printstmt = self.get_print_stmt(
                                node.value.args[0].left)
                            node.value.args[0].left = printstmt[0].targets[0]
                            stmt.extend(printstmt)
                            for i, c in enumerate(node.value.args[0].comparators):
                                printstmt2 = self.get_print_stmt(c)
                                stmt.extend(printstmt2)
                                node.value.args[0].comparators[i] = printstmt2[0].targets[0]
                        else:
                            for i, c in enumerate(node.value.args):
                                if i < 2:
                                    printstmt = self.get_print_stmt(c)
                                    stmt.extend(printstmt)
                                    node.value.args[i] = printstmt[0].targets[0]
                    stmt.append(node)
                    return stmt
        elif isinstance(node, ast.Assert):
            if node.lineno != self.assert_spec.line and self.assert_spec.line != -1:
                return node
            if isinstance(node.test, ast.Compare):
                stmt = []
                printstmt = self.get_print_stmt(node.test.left)
                node.test.left = printstmt[0].targets[0]
                stmt.extend(printstmt)
                for i, c in enumerate(node.test.comparators):
                    printstmt = self.get_print_stmt(c)
                    stmt.extend(printstmt)
                    node.test.comparators[i] = printstmt[0].targets[0]
                stmt.append(node)
                return stmt
            elif isinstance(node.test, ast.Call):
                # assert return value of a function
                stmt = []
                for i, c in enumerate(node.test.args):
                    if isinstance(c, ast.Name):
                        printstmt = self.get_print_stmt(c)
                        node.test.args[i] = printstmt[0].targets[0]
                        stmt.extend(printstmt)
                    elif isinstance(c, ast.Compare):
                        printstmt = self.get_print_stmt(c.left)
                        c.left = printstmt[0].targets[0]
                        stmt.extend(printstmt)
                        for ii, cc in enumerate(c.comparators):
                            printstmt = self.get_print_stmt(cc)
                            stmt.extend(printstmt)
                            c.comparators[ii] = printstmt[0].targets[0]
                stmt.append(node)
                return stmt

        self.generic_visit(node)
        return node
