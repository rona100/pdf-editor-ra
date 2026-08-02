import tempfile
import shutil
from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from ..pdf_operations import (
    RTL_MODES,
    convert_docx_to_pdf,
    convert_pdf_to_docx,
    merge_pdfs,
    order_pdf_pages,
    rotate_pdf_pages,
)

DOCX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

router = APIRouter()


@router.post("/rotate")
async def rotate(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    pages: str = Form(...),
    angle: int = Form(180),
):
    tmpdir = Path(tempfile.mkdtemp(prefix="pdf_editor_"))
    try:
        input_path = tmpdir / "input.pdf"
        output_path = tmpdir / "output.pdf"

        with open(input_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        try:
            pages_list = [int(p.strip()) for p in pages.split(",")]
        except ValueError:
            shutil.rmtree(tmpdir)
            raise HTTPException(422, "pages must be comma-separated integers")

        try:
            rotate_pdf_pages(str(input_path), str(output_path), pages_list, angle)
        except Exception as e:
            shutil.rmtree(tmpdir)
            raise HTTPException(500, str(e))

        background_tasks.add_task(shutil.rmtree, str(tmpdir), True)
        return FileResponse(
            str(output_path),
            media_type="application/pdf",
            filename="rotated.pdf",
        )
    except HTTPException:
        raise
    except Exception as e:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise HTTPException(500, str(e))


@router.post("/merge")
async def merge(
    background_tasks: BackgroundTasks,
    file1: UploadFile = File(...),
    file2: UploadFile = File(...),
):
    tmpdir = Path(tempfile.mkdtemp(prefix="pdf_editor_"))
    try:
        input_path1 = tmpdir / "file1.pdf"
        input_path2 = tmpdir / "file2.pdf"
        output_path = tmpdir / "merged.pdf"

        with open(input_path1, "wb") as f:
            shutil.copyfileobj(file1.file, f)

        with open(input_path2, "wb") as f:
            shutil.copyfileobj(file2.file, f)

        try:
            merge_pdfs(str(input_path1), str(input_path2), str(output_path))
        except Exception as e:
            shutil.rmtree(tmpdir)
            raise HTTPException(500, str(e))

        background_tasks.add_task(shutil.rmtree, str(tmpdir), True)
        return FileResponse(
            str(output_path),
            media_type="application/pdf",
            filename="merged.pdf",
        )
    except HTTPException:
        raise
    except Exception as e:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise HTTPException(500, str(e))


@router.post("/order")
async def order(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    num_pages: int = Form(...),
    new_order: str = Form(...),
):
    tmpdir = Path(tempfile.mkdtemp(prefix="pdf_editor_"))
    try:
        input_path = tmpdir / "input.pdf"
        output_path = tmpdir / "ordered.pdf"

        with open(input_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        try:
            order_pdf_pages(str(input_path), str(output_path), num_pages, new_order)
        except Exception as e:
            shutil.rmtree(tmpdir)
            raise HTTPException(500, str(e))

        background_tasks.add_task(shutil.rmtree, str(tmpdir), True)
        return FileResponse(
            str(output_path),
            media_type="application/pdf",
            filename="ordered.pdf",
        )
    except HTTPException:
        raise
    except Exception as e:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise HTTPException(500, str(e))


@router.post("/convert")
async def convert(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    rtl: str = Form("auto"),
):
    tmpdir = Path(tempfile.mkdtemp(prefix="pdf_editor_"))
    try:
        input_path = tmpdir / "input.pdf"
        output_path = tmpdir / "converted.docx"

        with open(input_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        if rtl not in RTL_MODES:
            shutil.rmtree(tmpdir)
            raise HTTPException(422, f"rtl must be one of {', '.join(RTL_MODES)}")

        try:
            convert_pdf_to_docx(str(input_path), str(output_path), rtl=rtl)
        except Exception as e:
            shutil.rmtree(tmpdir)
            raise HTTPException(500, str(e))

        background_tasks.add_task(shutil.rmtree, str(tmpdir), True)
        return FileResponse(
            str(output_path),
            media_type=DOCX_MEDIA_TYPE,
            filename="converted.docx",
        )
    except HTTPException:
        raise
    except Exception as e:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise HTTPException(500, str(e))


@router.post("/docx2pdf")
async def docx2pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    tmpdir = Path(tempfile.mkdtemp(prefix="pdf_editor_"))
    try:
        input_path = tmpdir / "input.docx"
        output_path = tmpdir / "converted.pdf"

        with open(input_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        try:
            convert_docx_to_pdf(str(input_path), str(output_path))
        except ValueError as e:
            # The upload is not a Word document — a client problem, not ours.
            shutil.rmtree(tmpdir)
            raise HTTPException(422, str(e))
        except Exception as e:
            shutil.rmtree(tmpdir)
            raise HTTPException(500, str(e))

        background_tasks.add_task(shutil.rmtree, str(tmpdir), True)
        return FileResponse(
            str(output_path),
            media_type="application/pdf",
            filename="converted.pdf",
        )
    except HTTPException:
        raise
    except Exception as e:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise HTTPException(500, str(e))
