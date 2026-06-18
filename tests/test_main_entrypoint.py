import main


def test_start_development_server_runs_uvicorn_with_local_dashboard_defaults(monkeypatch):
    capturedUvicornArguments = {}

    def fakeUvicornRun(applicationImportPath, host, port, reload):
        capturedUvicornArguments["applicationImportPath"] = applicationImportPath
        capturedUvicornArguments["host"] = host
        capturedUvicornArguments["port"] = port
        capturedUvicornArguments["reload"] = reload

    monkeypatch.setattr(main.uvicorn, "run", fakeUvicornRun)
    monkeypatch.setenv("UPWORK_RESEARCH_DASHBOARD_HOST", "127.0.0.1")
    monkeypatch.setenv("UPWORK_RESEARCH_DASHBOARD_PORT", "8000")

    main.startDevelopmentServer()

    assert capturedUvicornArguments == {
        "applicationImportPath": "main:app",
        "host": "127.0.0.1",
        "port": 8000,
        "reload": True,
    }
