"""Integration tests for the CLI, exercising the full argument-parsing + operations chain."""

import os
import subprocess
import sys
import tempfile

import pytest
from pypdf import PdfReader, PdfWriter


def make_test_pdf(pages: int = 3) -> str:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=612, height=792)
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    with open(tmp.name, "wb") as f:
        writer.write(f)
    return tmp.name


def run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "pdf_editor", *args],
        capture_output=True,
        text=True,
    )


class TestCLIHelp:
    def test_help_exits_zero(self):
        result = run_cli("--help")
        assert result.returncode == 0
        assert "rotate" in result.stdout

    def test_rotate_help_exits_zero(self):
        result = run_cli("rotate", "--help")
        assert result.returncode == 0

    def test_no_subcommand_exits_zero(self):
        result = run_cli()
        assert result.returncode == 0

    def test_unknown_subcommand_exits_nonzero(self):
        result = run_cli("unknown_command")
        assert result.returncode != 0


class TestCLIRotate:
    def test_rotate_produces_valid_output(self):
        input_pdf = make_test_pdf(3)
        output_pdf = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False).name
        try:
            result = run_cli("rotate", input_pdf, "1,2", "-o", output_pdf, "--angle", "90")
            assert result.returncode == 0
            with open(output_pdf, "rb") as f:
                reader = PdfReader(f)
                assert len(reader.pages) == 3
        finally:
            os.unlink(input_pdf)
            if os.path.exists(output_pdf):
                os.unlink(output_pdf)

    def test_rotate_default_angle_is_180(self):
        input_pdf = make_test_pdf(2)
        output_pdf = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False).name
        try:
            result = run_cli("rotate", input_pdf, "1", "-o", output_pdf)
            assert result.returncode == 0
            with open(output_pdf, "rb") as f:
                reader = PdfReader(f)
                assert reader.pages[0].rotation == 180
        finally:
            os.unlink(input_pdf)
            if os.path.exists(output_pdf):
                os.unlink(output_pdf)

    def test_rotate_long_flag_output(self):
        input_pdf = make_test_pdf(2)
        output_pdf = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False).name
        try:
            result = run_cli("rotate", input_pdf, "1", "--output", output_pdf, "--angle", "270")
            assert result.returncode == 0
            with open(output_pdf, "rb") as f:
                reader = PdfReader(f)
                assert reader.pages[0].rotation == 270
        finally:
            os.unlink(input_pdf)
            if os.path.exists(output_pdf):
                os.unlink(output_pdf)

    def test_rotate_invalid_pages_exits_nonzero(self):
        input_pdf = make_test_pdf(2)
        output_pdf = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False).name
        try:
            result = run_cli("rotate", input_pdf, "abc", "-o", output_pdf)
            assert result.returncode != 0
        finally:
            os.unlink(input_pdf)
            if os.path.exists(output_pdf):
                os.unlink(output_pdf)

    def test_rotate_missing_args_exits_nonzero(self):
        result = run_cli("rotate")
        assert result.returncode != 0


class TestCLIMerge:
    def test_merge_produces_combined_output(self):
        pdf1 = make_test_pdf(2)
        pdf2 = make_test_pdf(3)
        output_pdf = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False).name
        try:
            result = run_cli("merge", pdf1, pdf2, "-o", output_pdf)
            assert result.returncode == 0
            with open(output_pdf, "rb") as f:
                reader = PdfReader(f)
                assert len(reader.pages) == 5
        finally:
            os.unlink(pdf1)
            os.unlink(pdf2)
            if os.path.exists(output_pdf):
                os.unlink(output_pdf)

    def test_merge_nonexistent_input_exits_nonzero(self):
        output_pdf = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False).name
        try:
            result = run_cli("merge", "ghost1.pdf", "ghost2.pdf", "-o", output_pdf)
            assert result.returncode != 0
        finally:
            if os.path.exists(output_pdf):
                os.unlink(output_pdf)

    def test_merge_missing_args_exits_nonzero(self):
        result = run_cli("merge")
        assert result.returncode != 0


class TestCLIOrder:
    def test_order_reorders_pages(self):
        input_pdf = make_test_pdf(4)
        output_pdf = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False).name
        try:
            result = run_cli("order", input_pdf, "4", "4,3,2,1", "-o", output_pdf)
            assert result.returncode == 0
            with open(output_pdf, "rb") as f:
                reader = PdfReader(f)
                assert len(reader.pages) == 4
        finally:
            os.unlink(input_pdf)
            if os.path.exists(output_pdf):
                os.unlink(output_pdf)

    def test_order_partial_reorder_preserves_total_pages(self):
        input_pdf = make_test_pdf(6)
        output_pdf = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False).name
        try:
            result = run_cli("order", input_pdf, "3", "3,2,1", "-o", output_pdf)
            assert result.returncode == 0
            with open(output_pdf, "rb") as f:
                reader = PdfReader(f)
                assert len(reader.pages) == 6
        finally:
            os.unlink(input_pdf)
            if os.path.exists(output_pdf):
                os.unlink(output_pdf)

    def test_order_invalid_order_exits_nonzero(self):
        input_pdf = make_test_pdf(3)
        output_pdf = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False).name
        try:
            result = run_cli("order", input_pdf, "3", "1,1,3", "-o", output_pdf)
            assert result.returncode != 0
        finally:
            os.unlink(input_pdf)
            if os.path.exists(output_pdf):
                os.unlink(output_pdf)

    def test_order_missing_args_exits_nonzero(self):
        result = run_cli("order")
        assert result.returncode != 0


class TestCLIConvert:
    def test_convert_produces_docx(self):
        input_pdf = make_test_pdf(1)
        output_docx = tempfile.NamedTemporaryFile(suffix=".docx", delete=False).name
        try:
            result = run_cli("convert", input_pdf, "-o", output_docx)
            assert result.returncode == 0
            assert os.path.exists(output_docx)
            assert os.path.getsize(output_docx) > 0
        finally:
            os.unlink(input_pdf)
            if os.path.exists(output_docx):
                os.unlink(output_docx)

    def test_convert_missing_args_exits_nonzero(self):
        result = run_cli("convert")
        assert result.returncode != 0
