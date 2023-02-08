import astunparse
import sys
import os

import ast


class GetExtras(ast.NodeTransformer):
    def __init__(self, filename):
        self.filename = filename
        self.remove_others = False

    def run(self):
        a = ast.parse(open(self.filename, encoding='utf-8', errors='ignore').read())
        modified = self.visit(a)
        if self.remove_others is True:
            modified = ast.fix_missing_locations(modified)
            return astunparse.unparse(modified).strip()
        else:
            return ""

    def visit(self, node):
        if self.remove_others:
            return None
        else:
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id == 'setup':
                        # print(node.func.id)
                        for a in node.keywords:
                            if a.arg == 'extras_require':
                                # print(a.value)
                                self.remove_others = True
                                return [ast.Assign(targets=[ast.Name(id='xextra', ctx=ast.Store())], value=a.value),
                                        ast.parse("for ky in xextra.keys():\n    for kk in xextra[ky]:\n        print(\"dep>%s\" %kk)")]
            self.generic_visit(node)
            return node


if __name__ == '__main__':
    setupfile = sys.argv[1]
    outputfilename = "printExtra.py"
    getExtras = GetExtras(setupfile)
    result = getExtras.run()
    with open(os.path.join(os.path.dirname(setupfile), outputfilename), 'w', encoding='utf-8') as ofile:
        ofile.write(result)
