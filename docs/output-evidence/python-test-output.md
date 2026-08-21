# Python automated test output

## Command

```powershell
Set-Location C:\dev\git\GenAITraining\9CapstoneProject\AgenticRagSystem
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pytest -q tests
```

## Full local terminal output

```text
(.venv) PS C:\dev\git\GenAITraining\9CapstoneProject\AgenticRagSystem> python -m pytest -q tests             
.................................. [ 39%]
.................................. [ 78%]
...................                [100%]
=========== warnings summary ============
.venv\Lib\site-packages\fastapi\openapi\models.py:55
  C:\dev\git\GenAITraining\9CapstoneProject\AgenticRagSystem\.venv\Lib\site-packages\fastapi\openapi\models.py:55: DeprecationWarning: `general_plain_validator_function` is deprecated, use `with_info_plain_validator_function` instead.
    return general_plain_validator_function(cls._validate)

.venv\Lib\site-packages\pydantic_core\core_schema.py:4434
.venv\Lib\site-packages\pydantic_core\core_schema.py:4434
.venv\Lib\site-packages\pydantic_core\core_schema.py:4434
.venv\Lib\site-packages\pydantic_core\core_schema.py:4434
.venv\Lib\site-packages\pydantic_core\core_schema.py:4434
  C:\dev\git\GenAITraining\9CapstoneProject\AgenticRagSystem\.venv\Lib\site-packages\pydantic_core\core_schema.py:4434: DeprecationWarning: `general_plain_validator_function` is deprecated, use `with_info_plain_validator_function` instead.
    warnings.warn(

.venv\Lib\site-packages\starlette\formparsers.py:10
  C:\dev\git\GenAITraining\9CapstoneProject\AgenticRagSystem\.venv\Lib\site-packages\starlette\formparsers.py:10: PendingDeprecationWarning: Please use `import python_multipart` instead.
    import multipart

.venv\Lib\site-packages\fastapi\datastructures.py:52
.venv\Lib\site-packages\fastapi\datastructures.py:52
.venv\Lib\site-packages\fastapi\datastructures.py:52
.venv\Lib\site-packages\fastapi\datastructures.py:52
  C:\dev\git\GenAITraining\9CapstoneProject\AgenticRagSystem\.venv\Lib\site-packages\fastapi\datastructures.py:52: DeprecationWarning: `general_plain_validator_function` is deprecated, use `with_info_plain_validator_function` instead.
    return general_plain_validator_function(cls._validate)

tests/test_analysis_api.py: 6 warnings
tests/test_ask_api.py: 3 warnings
tests/test_documents_api.py: 4 warnings
tests/test_health_api.py: 1 warning
tests/test_logging.py: 1 warning
tests/test_search_api.py: 3 warnings
  C:\dev\git\GenAITraining\9CapstoneProject\AgenticRagSystem\.venv\Lib\site-packages\httpx\_client.py:690: DeprecationWarning: The 'app' shortcut is now deprecated. Use the explicit style 'transport=WSGITransport(app=...)' instead.
    warnings.warn(message, DeprecationWarning)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
87 passed, 29 warnings in 6.75s
```

## Notes

- All automated tests passed.
- Warnings are dependency deprecation warnings from FastAPI/Pydantic/Starlette/httpx test tooling.
- No test failures were reported.

