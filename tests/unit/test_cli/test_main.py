"""
Unit tests for CLI main module.
"""

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from src.cli.main import cli, main


class TestCLIMain:
    """Test cases for CLI main module."""

    def test_main_cli_initialization(self) -> None:
        """Test that main CLI function exists."""
        assert callable(main)
        assert callable(cli)

    def test_main_cli_group(self) -> None:
        """Test CLI group structure."""
        runner = CliRunner()

        # Test that cli is a Click group
        result = runner.invoke(cli, ["--help"])

        # Should show help
        assert result.exit_code == 0
        assert "Usage:" in result.output or "Commands:" in result.output

    def test_cli_function_call(self) -> None:
        """Test cli() function body is executed (covers line 29 pass statement)."""
        runner = CliRunner()
        # Invoke cli with --help to ensure function body (pass) is executed
        # The pass statement on line 29 is executed when the function is called
        result = runner.invoke(cli, ["--help"])
        # Should show help (exit code 0) - this ensures cli() function body executes
        assert result.exit_code == 0
        # The pass statement in cli() is executed when the function is invoked

    def test_cli_function_direct_call(self) -> None:
        """Test cli() function can be called directly (covers line 29 pass statement)."""
        # Get the callback function from the Click command
        # Click decorator wraps the function, so we need to access the callback
        callback = cli.callback if hasattr(cli, "callback") else cli
        # Call the callback directly to ensure pass statement is executed
        callback()  # This should execute the pass statement on line 29
        # If no exception is raised, the function executed successfully

    def test_cli_version_option(self) -> None:
        """Test CLI version option."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "0.1.0" in result.output
        assert "upbit-quant" in result.output

    @patch("src.cli.main.cli")
    def test_main_function(self, mock_cli: MagicMock) -> None:
        """Test main() function calls cli() (line 40)."""
        main()
        mock_cli.assert_called_once()


class TestMainModule:
    """Test cases for src.main module."""

    def test_main_module_import(self) -> None:
        """Test that src.main can be imported (covers line 7)."""
        # Importing the module should execute line 7
        import src.main

        # Verify main function is accessible
        assert hasattr(src.main, "main")
        assert callable(src.main.main)

    def test_main_module_execution(self) -> None:
        """Test src.main execution when run as script."""
        import src.main

        # The module should have main function from cli.main
        from src.cli.main import main as cli_main

        assert src.main.main == cli_main
