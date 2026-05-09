import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = PROJECT_ROOT / "src" / "coverai"

FORBIDDEN_LAYER_IMPORTS = {
    "domain": {"services", "infra", "bot", "workers", "repos", "clients"},
    "services": {"infra", "bot", "workers", "repos", "clients"},
    "repos": {"bot", "workers"},
    "clients": {"bot", "workers"},
}


def python_files_under(*roots: Path) -> list[Path]:
    files: list[Path] = []

    for root in roots:
        files.extend(
            path
            for path in root.rglob("*.py")
            if "__pycache__" not in path.parts
        )

    return sorted(files)


def parse_python(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def layer_for_path(path: Path) -> str | None:
    relative = path.relative_to(PACKAGE_ROOT)
    return relative.parts[0] if relative.parts else None


def imported_modules(path: Path, tree: ast.Module) -> list[str]:
    modules: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.append(resolve_import_from(path, node))

    return [module for module in modules if module]


def resolve_import_from(path: Path, node: ast.ImportFrom) -> str:
    if node.level == 0:
        return node.module or ""

    relative = path.relative_to(PROJECT_ROOT).with_suffix("")
    current_parts = list(relative.parts)
    if current_parts[-1] != "__init__":
        current_parts = current_parts[:-1]

    base = current_parts[: len(current_parts) - node.level + 1]
    module_parts = node.module.split(".") if node.module else []

    return ".".join([*base, *module_parts])


def coverai_layer(module: str) -> str | None:
    parts = module.split(".")
    if len(parts) < 2 or parts[0] != "coverai":
        return None

    return parts[1]


def test_package_does_not_import_old_src_package() -> None:
    checked_roots = [
        PROJECT_ROOT / "src",
        PROJECT_ROOT / "tests",
        PROJECT_ROOT / "alembic",
    ]

    offenders: list[str] = []
    for path in python_files_under(*checked_roots):
        tree = parse_python(path)
        for module in imported_modules(path, tree):
            if module == "src" or module.startswith("src."):
                offenders.append(f"{path.relative_to(PROJECT_ROOT)} imports {module}")

    assert offenders == []


def test_package_does_not_use_future_annotations() -> None:
    checked_roots = [
        PROJECT_ROOT / "src",
        PROJECT_ROOT / "tests",
        PROJECT_ROOT / "alembic",
    ]

    offenders: list[str] = []
    for path in python_files_under(*checked_roots):
        tree = parse_python(path)
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom) or node.module != "__future__":
                continue

            imported_names = {alias.name for alias in node.names}
            if "annotations" in imported_names:
                offenders.append(str(path.relative_to(PROJECT_ROOT)))

    assert offenders == []


def test_layer_import_direction() -> None:
    offenders: list[str] = []

    for path in python_files_under(PACKAGE_ROOT):
        source_layer = layer_for_path(path)
        if source_layer not in FORBIDDEN_LAYER_IMPORTS:
            continue

        tree = parse_python(path)
        forbidden_layers = FORBIDDEN_LAYER_IMPORTS[source_layer]

        for module in imported_modules(path, tree):
            target_layer = coverai_layer(module)
            if target_layer in forbidden_layers:
                offenders.append(
                    f"{path.relative_to(PROJECT_ROOT)} imports forbidden {module}",
                )

    assert offenders == []


def test_services_do_not_import_sqlalchemy() -> None:
    offenders: list[str] = []
    services_root = PACKAGE_ROOT / "services"

    for path in python_files_under(services_root):
        tree = parse_python(path)
        for module in imported_modules(path, tree):
            if module == "sqlalchemy" or module.startswith("sqlalchemy."):
                offenders.append(
                    f"{path.relative_to(PROJECT_ROOT)} imports forbidden {module}",
                )

    assert offenders == []


def test_domain_and_services_do_not_import_prometheus() -> None:
    offenders: list[str] = []
    checked_roots = [
        PACKAGE_ROOT / "domain",
        PACKAGE_ROOT / "services",
    ]

    for path in python_files_under(*checked_roots):
        tree = parse_python(path)
        for module in imported_modules(path, tree):
            if module == "prometheus_client" or module.startswith(
                "prometheus_client.",
            ):
                offenders.append(
                    f"{path.relative_to(PROJECT_ROOT)} imports forbidden {module}",
                )

    assert offenders == []


def test_fake_repositories_do_not_import_sqlalchemy() -> None:
    offenders: list[str] = []
    fakes_root = PROJECT_ROOT / "tests" / "fakes"

    for path in python_files_under(fakes_root):
        tree = parse_python(path)
        for module in imported_modules(path, tree):
            if module == "sqlalchemy" or module.startswith("sqlalchemy."):
                offenders.append(
                    f"{path.relative_to(PROJECT_ROOT)} imports forbidden {module}",
                )

    assert offenders == []
