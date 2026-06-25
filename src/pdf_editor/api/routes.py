import tempfile
import shutil
from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from ..pdf_operations import rotate_pdf_pages, merge_pdfs, order_pdf_pages, convert_pdf_to_docx

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
):
    tmpdir = Path(tempfile.mkdtemp(prefix="pdf_editor_"))
    try:
        input_path = tmpdir / "input.pdf"
        output_path = tmpdir / "converted.docx"

        with open(input_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        try:
            convert_pdf_to_docx(str(input_path), str(output_path))
        except Exception as e:
            shutil.rmtree(tmpdir)
            raise HTTPException(500, str(e))

        background_tasks.add_task(shutil.rmtree, str(tmpdir), True)
        return FileResponse(
            str(output_path),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename="converted.docx",
        )
    except HTTPException:
        raise
    except Exception as e:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise HTTPException(500, str(e))
