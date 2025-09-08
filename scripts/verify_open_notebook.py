import sys

def main() -> int:
    try:
        import streamlit  # type: ignore
        import fastapi  # type: ignore
        import uvicorn  # type: ignore
        import open_notebook  # type: ignore
    except Exception as e:
        print(f"import_error: {e}")
        return 1

    print(
        "versions",
        "streamlit",
        getattr(streamlit, "__version__", "?"),
        "fastapi",
        getattr(fastapi, "__version__", "?"),
        "uvicorn",
        getattr(uvicorn, "__version__", "?"),
    )
    print("open_notebook_import", True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

