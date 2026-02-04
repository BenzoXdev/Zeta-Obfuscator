import marshal
import random
import string
import ast
import zlib
import base64
import builtins
import sys
import os
import datetime
import colorama
import ctypes
import tkinter as tk
from tkinter import filedialog
import shutil
import time
from colorama import init, Fore, Style
init(autoreset=True)

color = colorama.Fore
red = color.RED
white = color.WHITE
green = color.GREEN
reset = color.RESET
BEFORE = f'{red}[{white}'
AFTER = f'{red}]'
INPUT = f'{BEFORE}>{AFTER} |'
INFO = f'{BEFORE}!{AFTER} |'
ERROR = f'{BEFORE}x{AFTER} |'
ADD = f'{BEFORE}+{AFTER} |'
WAIT = f'{BEFORE}~{AFTER} |'
github = 'github.com/BenzoXdev'
telegram = 't.me/benzoXdev'
instagram = 'instagram.com/just._.amar_x1'
by = 'BenzoXdev'
folder = 'Zeta-Obfuscator'
output_folder_1 = os.path.join(folder, 'Script-Obfuscate')
script_folder = os.path.join(folder, 'Script')
txt_file = os.path.join(folder, 'README.txt')

def current_time_hour():
    return datetime.datetime.now().strftime('%H:%M:%S')

def Title(title):
    if sys.platform.startswith('win'):
        ctypes.windll.kernel32.SetConsoleTitleW(f'Zeta-Obfuscator - Obfuscator Tool | {title}')
    else:
        if sys.platform.startswith('linux'):
            sys.stdout.write(f'\033]2;Zeta-Obfuscator - Obfuscator Tool | {title}\a')

def Clear():
    if sys.platform.startswith('win'):
        os.system('cls')
    else:
        if sys.platform.startswith('linux'):
            os.system('clear')

Clear()

def ChoosePythonFile():
    """Retourne une liste de chemins de fichiers Python (selection fenetre ou saisie manuelle)."""
    ts = BEFORE + current_time_hour() + AFTER
    print(f'{ts} {INPUT} Choisissez un fichier Python -> {reset}')
    chosen = []
    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        # Selection multiple possible
        python_files = filedialog.askopenfilenames(
            parent=root,
            title='Zeta-Obfuscator - Obfuscator Tool | Choisir un ou plusieurs fichiers Python (.py)',
            filetypes=[('Fichiers PYTHON', '*.py')]
        )
        if python_files:
            chosen = list(python_files)
            for p in chosen:
                print(f'{ts} {ADD} Fichier choisi : {white}{p}{reset}')
            return chosen
    except Exception:
        pass
    # Pas de fichier choisi via la fenetre : proposer la saisie manuelle
    print(f'{ts} {INFO} Aucun fichier selectionne. Saisir le(s) chemin(s) manuellement ?')
    try:
        rep = input(f'{ts} {INPUT} Entrer le(s) chemin(s) (separes par des virgules) ou un seul chemin -> {reset}').strip()
    except KeyboardInterrupt:
        print()
        return []
    if rep:
        chosen = [x.strip() for x in rep.split(',') if x.strip()]
        for p in chosen:
            print(f'{ts} {ADD} Fichier saisi : {white}{p}{reset}')
    return chosen

def random_var(used_vars, number=10):
    # Ne jamais generer un nom qui shadow un builtin (evite "int" object is not callable)
    forbidden = used_vars | _BUILTINS | {"int", "type", "str", "list", "dict", "set", "add", "exec", "eval", "id", "sum", "min", "max", "map", "filter", "range", "len", "open", "print", "input"}
    while True:
        rdm_var = ''.join(random.choices(string.ascii_letters, k=number))
        if rdm_var not in forbidden:
            used_vars.add(rdm_var)
            return rdm_var


# --- Noms à ne jamais renommer (compat .py + .exe) ---
_BUILTINS = set(dir(builtins)) | {'__name__', '__file__', '__doc__', '__builtins__', '__import__'}


# --- Suppression docstrings uniquement (1re chaine par bloc = docstring) ---
def strip_comments_docstrings(code):
    """Supprime les docstrings via AST (seule la 1re Expr(Constant(str)) par bloc)."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            body = node.body if isinstance(node, ast.Module) else node.body
            for i, child in enumerate(body):
                if isinstance(child, ast.Expr) and isinstance(child.value, ast.Constant) and isinstance(child.value.value, str):
                    # Garder le 1er caractère pour que __doc__[:1] reste valide
                    s = child.value.value
                    body[i] = ast.Expr(ast.Constant(value=(s[:1] if s else "")))
                    break  # une seule docstring par bloc
    try:
        return ast.unparse(tree)
    except AttributeError:
        return code
    except Exception:
        return code


# --- Inspiré ObfuXtreme : collecte variables (assigned, globals, args) ---
class _VariableCollector(ast.NodeVisitor):
    def __init__(self):
        self.assigned = set()
        self.globals = set()
        self.args = set()
        self.nonlocals = set()

    def visit_Global(self, node):
        self.globals.update(node.names)

    def visit_Nonlocal(self, node):
        self.nonlocals.update(node.names)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Store):
            self.assigned.add(node.id)

    def visit_arg(self, node):
        self.args.add(node.arg)
        self.assigned.add(node.arg)


class _CallableNameCollector(ast.NodeVisitor):
    """Collecte les noms utilises comme appelable (func dans Call) pour ne pas les renommer."""
    def __init__(self):
        self.names = set()

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            self.names.add(node.func.id)
        self.generic_visit(node)


# --- Inspiré ObfuXtreme/BlankOBF : renommage variables locales (_0x hex) ---
class _VariableRenamer(ast.NodeTransformer):
    def __init__(self, assigned, args, globals_, nonlocals_, callable_names=None):
        # Ne pas renommer builtins, args, globals, nonlocals, noms __xxx__, ni noms appeles comme fonctions
        protected = set(args) | set(globals_) | set(nonlocals_) | _BUILTINS | (callable_names or set())
        protected |= {n for n in assigned if (n.startswith("__") and n.endswith("__"))}
        self.rename_set = set(assigned) - protected
        self._map = {}

    def _new_name(self):
        return "_0x" + "".join(random.choices(string.hexdigits[:16], k=random.randint(12, 20)))

    def visit_Name(self, node):
        if node.id in self.rename_set:
            if node.id not in self._map:
                self._map[node.id] = self._new_name()
            node.id = self._map[node.id]
        return node


# --- Inspiré BlankOBFv2 : obfuscation constantes (int arithmétique, str bytes) ---
class _ConstantObfuscator(ast.NodeTransformer):
    """Compat .py et .exe : uniquement stdlib (bytes, getattr, etc.)."""
    def __init__(self):
        self._in_joined_str = False
        self._in_match_pattern = False
        self._in_type_call_arg = False

    def visit_JoinedStr(self, node):
        self._in_joined_str = True
        self.generic_visit(node)
        self._in_joined_str = False
        return node

    def visit_match_case(self, node):
        """Ne pas obfusquer les constantes dans les patterns match/case (sinon SyntaxError)."""
        self._in_match_pattern = True
        node.pattern = self.visit(node.pattern)
        self._in_match_pattern = False
        if node.guard is not None:
            node.guard = self.visit(node.guard)
        for i in range(len(node.body)):
            node.body[i] = self.visit(node.body[i])
        return node

    def visit_Call(self, node):
        # Ne pas obfusquer l'argument de type(...) pour eviter tout conflit
        if isinstance(node.func, ast.Name) and node.func.id == "type" and len(node.args) == 1:
            self._in_type_call_arg = True
            node.args = [self.visit(a) for a in node.args]
            self._in_type_call_arg = False
            if node.keywords:
                node.keywords = [self.visit(kw) for kw in node.keywords]
            return node
        return self.generic_visit(node)

    def visit_Constant(self, node):
        if self._in_joined_str:
            return node
        if getattr(self, "_in_match_pattern", False):
            return node
        if getattr(self, "_in_type_call_arg", False):
            return node
        if isinstance(node.value, bool) or node.value is None:
            return node
        if isinstance(node.value, int):
            n = random.randint(2**12, 2**20)
            a = node.value * n
            b = node.value * (n - 1)
            return ast.BinOp(left=ast.Constant(a), op=ast.Sub(), right=ast.Constant(b))
        if isinstance(node.value, str):
            if len(node.value) > 500:
                return node
            try:
                enc = list(node.value.encode("utf-8"))[::-1]
            except Exception:
                return node
            list_ast = ast.List(elts=[ast.Constant(x) for x in enc], ctx=ast.Load())
            slice_ast = ast.Slice(lower=None, upper=None, step=ast.Constant(-1))
            sub = ast.Subscript(value=list_ast, slice=slice_ast, ctx=ast.Load())
            return ast.Call(
                func=ast.Attribute(
                    value=ast.Call(ast.Name("bytes", ast.Load()), [sub], []),
                    attr="decode",
                    ctx=ast.Load(),
                ),
                args=[ast.Constant("utf-8")],
                keywords=[],
            )
        if isinstance(node.value, bytes):
            if len(node.value) > 200:
                return node
            enc = list(node.value)[::-1]
            list_ast = ast.List(elts=[ast.Constant(x) for x in enc], ctx=ast.Load())
            slice_ast = ast.Slice(lower=None, upper=None, step=ast.Constant(-1))
            sub = ast.Subscript(value=list_ast, slice=slice_ast, ctx=ast.Load())
            return ast.Call(ast.Name("bytes", ast.Load()), [sub], [])
        return node


def ast_obfuscate(code):
    """Applique renommage variables + obfuscation constantes (AST). Compat .py et .exe."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code
    try:
        vc = _VariableCollector()
        vc.visit(tree)
        callable_collector = _CallableNameCollector()
        callable_collector.visit(tree)
        # Proteger aussi les noms de classes (utilises comme ClassName() pour instancier)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                callable_collector.names.add(node.name)
        for transformer in (
            _VariableRenamer(vc.assigned, vc.args, vc.globals, vc.nonlocals, callable_collector.names),
            _ConstantObfuscator(),
        ):
            tree = transformer.visit(tree)
            ast.fix_missing_locations(tree)
        return ast.unparse(tree)
    except Exception:
        return code


def layer_1(script):
    # Garde anti-modification : nom aleatoire pour eviter pattern fixe
    guard_var = random_var(set(), number=random.randint(8, 16))
    anti_kids_code = f'\n{guard_var} = 1\ntry:\n    {guard_var}\nexcept:\n    import sys\n    input("ERROR: The obfuscated code was modified. Please do not modify the obfuscated code.")\n    sys.exit()\n'
    script = anti_kids_code + script
    return script

# --- Inspiré BlankOBFv2 : couche base64 + zlib (payload en 4 parties) ---
def layer_b64(script):
    """Encode le script en base64+zlib réparti en 4 variables (style BlankOBF layer_1)."""
    encoded = base64.b64encode(zlib.compress(script.encode('utf-8'), 9)).decode('ascii')
    n = 4
    size = len(encoded)
    if size == 0:
        parts = ['', '', '', '']
    else:
        part_len = max(1, (size + n - 1) // n)
        parts = [encoded[i*part_len:(i+1)*part_len] for i in range(n)]
        parts = (parts + [''] * n)[:n]
    used = set()
    var_names = [random_var(used) for _ in range(n)]
    assigns = '\n'.join(f'{var_names[i]} = {repr(parts[i])}' for i in range(n))
    concat = ' + '.join(var_names)
    return f'{assigns}\n_exec_src_ = __import__("zlib").decompress(__import__("base64").b64decode({concat})).decode("utf-8")\nexec(_exec_src_)'


def layer_2(script, size_1, size_2):
    used_vars = set()
    for i in range(random.randint(size_1, size_2)):
        var_1 = random_var(used_vars, number=random.randint(size_1, size_2))
        var_2 = random_var(used_vars, number=random.randint(size_1, size_2))
        var_3 = random_var(used_vars, number=random.randint(size_1, size_2))
        var_4 = random_var(used_vars, number=random.randint(size_1, size_2))
        var_5 = random_var(used_vars, number=random.randint(size_1, size_2))
        var_6 = random_var(used_vars, number=random.randint(size_1, size_2))
        script = script + f'\nclass {var_1}:\n def {var_2}({var_3}):\n  {var_4} = {var_3}\n  {var_5} = {var_4}\n  return {var_5}\n {var_3} = \'{var_6}\'\n {var_5} = {var_2}({var_3})\n{var_1}()\n'
    for i in range(random.randint(size_1, size_2)):
        var_1 = random_var(used_vars, number=random.randint(size_1, size_2))
        var_2 = random_var(used_vars, number=random.randint(size_1, size_2))
        var_3 = random_var(used_vars, number=random.randint(size_1, size_2))
        var_4 = random_var(used_vars, number=random.randint(size_1, size_2))
        var_5 = random_var(used_vars, number=random.randint(size_1, size_2))
        var_6 = random_var(used_vars, number=random.randint(size_1, size_2))
        script = f'\nclass {var_1}:\n def {var_2}({var_3}):\n  {var_4} = {var_3}\n  {var_5} = {var_4}\n  return {var_5}\n {var_3} = \'{var_6}\'\n {var_5} = {var_2}({var_3})\n{var_1}()\n' + script
    return script

def layer_3(script):
    used_vars = set()
    key = random.randint(1, 5)  # 1-5 pour rester dans la plage Unicode
    var_1 = random_var(used_vars)
    var_2 = random_var(used_vars)
    var_3 = random_var(used_vars)
    max_codepoint = 0x10FFFF - key
    obfuscated_script = ''.join(
        chr(ord(c) + key) if ord(c) <= max_codepoint else c for c in script
    )
    # Decode: si ord(c) >= key c'est un caractere decale, sinon on garde c
    script = f'{var_1} = {repr(obfuscated_script)}\n{var_3} = {key}\n{var_2} = \'\'.join(chr(ord(c) - {var_3}) if ord(c) >= {var_3} else c for c in {var_1})\nexec({var_2})'
    return script

def layer_4(script):
    # Bytecode compilé + zlib (inspiré ObfuXtreme)
    compiled_code = marshal.dumps(compile(script, '<string>', 'exec'))
    compressed = zlib.compress(compiled_code, 9)
    script = f'_Zeta_Obfuscator_ = {repr(compressed)}\nexec(__marshal_loader__.loads(__zlib_decompress__(_Zeta_Obfuscator_)))'
    return script

def layer_5(script):
    chunk_size = random.randint(800, 1200)
    chunks = [script[i:i + chunk_size] for i in range(0, len(script), chunk_size)]
    used_vars = set()
    chunk_vars = {random_var(used_vars): repr(chunk) for chunk in chunks}
    code_vars = '\n    '.join((f'{k} = {v}' for k, v in chunk_vars.items()))
    chunk_keys = list(chunk_vars.keys())
    join_parts = ', '.join(f'_ZetaChunks.{k}' for k in chunk_keys)
    # _ZetaChunks garde les morceaux ; loaders pour layer_4 (marshal + zlib, inspiré ObfuXtreme)
    script = f"\nclass _ZetaChunks:\n    {code_vars}\n\n__marshal_loader__ = __import__('marshal')\n__zlib_decompress__ = __import__('zlib').decompress\n_code = ''.join([{join_parts}])\nexec(_code)"
    return script

def obfuscate(script, size_1, size_2, strip_docstrings=True, use_b64_layer=False, use_ast_obfuscate=True):
    """Pipeline d'obfuscation. Sortie compatible .py et .exe (stdlib uniquement)."""
    if strip_docstrings:
        script = strip_comments_docstrings(script)
    if use_ast_obfuscate:
        script = ast_obfuscate(script)
    script = layer_1(script)
    if use_b64_layer:
        script = layer_b64(script)
    script = layer_2(script, size_1, size_2)
    script = layer_3(script)
    script = layer_4(script)
    script = layer_5(script)
    return script

def Zeta_Obfuscator():
    Clear()
    Title(f'By: {by}')
    print(f'''{red}                                                                                                  

                                            ▒███████▒▓█████▄▄▄█████▓ ▄▄▄      
                                            ▒ ▒ ▒ ▄▀░▓█   ▀▓  ██▒ ▓▒▒████▄    
                                            ░ ▒ ▄▀▒░ ▒███  ▒ ▓██░ ▒░▒██  ▀█▄  
                                              ▄▀▒   ░▒▓█  ▄░ ▓██▓ ░ ░██▄▄▄▄██ 
                                            ▒███████▒░▒████▒ ▒██▒ ░  ▓█   ▓██▒
                                            ░▒▒ ▓░▒░▒░░ ▒░ ░ ▒ ░░    ▒▒   ▓▒█░
                                            ░░▒ ▒ ░ ▒ ░ ░  ░   ░      ▒   ▒▒ ░
                                            ░ ░ ░ ░ ░   ░    ░        ░   ▒   
                                              ░ ░       ░  ░              ░  ░
                                            ░                                 
                                 
{white}                                              GitHub : {github}

                                                  ╔═════════════════╗
                                                  ║ {red}Obfuscator Tool{white} ║
                                                  ╚═════════════════╝

{red}[{white}>{red}]{red} Telegram : {white}{telegram}
{red}[{white}>{red}]{red} Instagram : {white}{instagram}
''')


    files_python = ChoosePythonFile()
    if not files_python:
        print(f'{BEFORE + current_time_hour() + AFTER} {ERROR} Aucun fichier selectionne.')
        return
    ts = BEFORE + current_time_hour() + AFTER
    # Verifier que tous les fichiers existent
    valid_files = []
    for fp in files_python:
        if os.path.isfile(fp):
            valid_files.append(fp)
        else:
            print(f'{ts} {ERROR} Fichier introuvable : {fp}')
    if not valid_files:
        print(f'{ts} {ERROR} Aucun fichier valide.')
        return
    print(f'''
    {red}[{white}1{red}] {white}Weak
    {red}[{white}2{red}] {white}Medium
    {red}[{white}3{red}] {white}Strong
    {red}[{white}4{red}] {white}Very Strong
    {red}[{white}5{red}] {white}Extreme (Very Strong + Base64/Zlib)
    ''')
    try:
        obfuscation_force = int(input(f'{ts} {INPUT} Niveau d\'obfuscation (1-5) -> {reset}'))
    except ValueError:
        print(f'{ts} {ERROR} Nombre invalide.')
        return
    if obfuscation_force == 1:
        size_1, size_2, use_b64_layer = 8, 15, False
    elif obfuscation_force == 2:
        size_1, size_2, use_b64_layer = 10, 25, False
    elif obfuscation_force == 3:
        size_1, size_2, use_b64_layer = 30, 50, False
    elif obfuscation_force == 4:
        size_1, size_2, use_b64_layer = 50, 100, False
    elif obfuscation_force == 5:
        size_1, size_2, use_b64_layer = 50, 100, True
    else:
        print(f'{ts} {ERROR} Choisissez 1 a 5.')
        return

    print(f'{ts} {WAIT} Suppression des dossiers precedents..')
    if os.path.isdir(folder):
        shutil.rmtree(folder)
    time.sleep(1)
    print(f'{ts} {INFO} Dossiers precedents supprimes.')
    print(f'{ts} {INFO} Creation du dossier : {white}{folder}{reset}')
    os.mkdir(folder)
    time.sleep(1)
    print(f'{ts} {INFO} Creation du dossier : {white}{output_folder_1}{reset}')
    os.mkdir(output_folder_1)
    print(f'{ts} {INFO} Creation du dossier : {white}{script_folder}{reset}')
    os.mkdir(script_folder)
    time.sleep(1)
    used_names = {}
    for file_python in valid_files:
        base_name = os.path.basename(file_python)
        if base_name not in used_names:
            used_names[base_name] = 0
        else:
            used_names[base_name] += 1
        if used_names[base_name] == 0:
            file_name = base_name
        else:
            base, ext = os.path.splitext(base_name)
            file_name = f'{base}_{used_names[base_name]}{ext}'
        with open(file_python, 'r', encoding='utf-8') as file:
            script = file.read()
        script_path = os.path.join(script_folder, file_name)
        output_path = os.path.join(output_folder_1, file_name)
        print(f'{ts} {INFO} Copie du script : {white}{file_name}{reset} -> {script_path}')
        with open(script_path, 'w', encoding='utf-8') as file:
            file.write(script)
        print(f'{ts} {WAIT} Obfuscation en cours : {white}{file_name}{reset}..')
        obfuscated_script = obfuscate(script, size_1, size_2, strip_docstrings=False, use_b64_layer=use_b64_layer, use_ast_obfuscate=False)
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(obfuscated_script)
        print(f'{ts} {ADD} Termine : {white}{output_path}{reset}')
    print(f'{ts} {INFO} Obfuscation terminee : {len(valid_files)} fichier(s) -> {white}{output_folder_1}{reset}')
    print(f'{ts} {INFO} Scripts compatibles .py et .exe (PyInstaller, etc.)')

if __name__ == "__main__":
    try:
        while True:
            Zeta_Obfuscator()
            try:
                input(f'{BEFORE + current_time_hour() + AFTER} {INPUT} Press to continue.. ')
            except KeyboardInterrupt:
                print()
                break
    except KeyboardInterrupt:
        print()
