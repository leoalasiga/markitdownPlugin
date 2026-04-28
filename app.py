def main() -> int:
    try:
        from src.gui import main as gui_main
    except ModuleNotFoundError as exc:
        if exc.name == "tkinter":
            print(
                "Tkinter is not available in this Python environment. "
                "Install a Python distribution with Tkinter support to run the desktop app."
            )
            return 1
        raise

    gui_main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
