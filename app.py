def main() -> int:
    try:
        from src.gui import main as gui_main
    except ModuleNotFoundError as exc:
        if exc.name in {"flet", "tkinter"}:
            print(
                "Flet is not available in this Python environment. "
                "Run: py -m pip install -r requirements.txt"
            )
            return 1
        raise

    try:
        gui_main()
    except ModuleNotFoundError as exc:
        if exc.name == "flet" or "Flet is not installed" in str(exc):
            print("Flet is not installed. Run: py -m pip install -r requirements.txt")
            return 1
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
