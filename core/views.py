from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import FileResponse
from .converter import convert_file
from .document_tools import compress_pdf, compress_image, merge_pdfs, split_pdf, ai_summarize
import os
import tempfile
import zipfile

# ── ALLOWED FILE TYPES ───────────────────────────────────────────
ALLOWED_EXTENSIONS = [
    '.pdf', '.doc', '.docx', '.jpg', '.jpeg',
    '.png', '.pptx', '.xlsx', '.xls', '.txt'
]
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB

def allowed_file(filename):
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS

def file_size_ok(file):
    return file.size <= MAX_FILE_SIZE

# ── HOME ─────────────────────────────────────────────────────────
def home(request):
    return render(request, 'core/home.html')

# ── DASHBOARD ────────────────────────────────────────────────────
def dashboard(request):
    return render(request, 'core/dashboard.html')

# ── UPLOAD ───────────────────────────────────────────────────────
def upload(request):
    if request.method == 'POST' and request.FILES.get('file'):
        f = request.FILES['file']
        if not allowed_file(f.name):
            messages.error(request, 'File type not allowed. Please upload PDF, Word, Image, Excel or PPTX files only.')
            return redirect('upload')
        if not file_size_ok(f):
            messages.error(request, 'File too large. Maximum file size is 20MB.')
            return redirect('upload')
        messages.success(request, f'"{f.name}" uploaded successfully!')
        return redirect('dashboard')
    return render(request, 'core/upload.html')

# ── DOWNLOAD & DELETE ────────────────────────────────────────────
def download(request, doc_id):
    return redirect('dashboard')

def delete(request, doc_id):
    return redirect('dashboard')

# ── CONVERT ──────────────────────────────────────────────────────
def convert(request):
    pdf_conversions = [
        ('pdf_to_word',  'PDF → Word (.docx)'),
        ('pdf_to_jpg',   'PDF → JPG'),
        ('pdf_to_png',   'PDF → PNG'),
        ('pdf_to_excel', 'PDF → Excel (.xlsx)'),
        ('pdf_to_pptx',  'PDF → PowerPoint (.pptx)'),
    ]
    word_conversions = [
        ('word_to_pdf', 'Word → PDF'),
        ('word_to_jpg', 'Word → JPG'),
        ('word_to_png', 'Word → PNG'),
    ]
    image_conversions = [
        ('jpg_to_pdf', 'JPG → PDF'),
        ('jpg_to_png', 'JPG → PNG'),
        ('png_to_pdf', 'PNG → PDF'),
        ('png_to_jpg', 'PNG → JPG'),
    ]
    other_conversions = [
        ('excel_to_pdf', 'Excel → PDF'),
        ('pptx_to_pdf',  'PowerPoint → PDF'),
    ]
    return render(request, 'core/convert.html', {
        'pdf_conversions':   pdf_conversions,
        'word_conversions':  word_conversions,
        'image_conversions': image_conversions,
        'other_conversions': other_conversions,
    })

def do_convert(request):
    if request.method == 'POST' and request.FILES.get('file'):
        f = request.FILES['file']
        if not allowed_file(f.name):
            messages.error(request, 'File type not allowed.')
            return redirect('convert')
        if not file_size_ok(f):
            messages.error(request, 'File too large. Maximum size is 20MB.')
            return redirect('convert')
        conversion_type = request.POST.get('conversion_type')
        ext_map = {
            'pdf_to_word':  '.docx',
            'pdf_to_jpg':   '.jpg',
            'pdf_to_png':   '.png',
            'pdf_to_excel': '.xlsx',
            'pdf_to_pptx':  '.pptx',
            'word_to_pdf':  '.pdf',
            'word_to_jpg':  '.jpg',
            'word_to_png':  '.png',
            'jpg_to_pdf':   '.pdf',
            'jpg_to_png':   '.png',
            'png_to_pdf':   '.pdf',
            'png_to_jpg':   '.jpg',
            'excel_to_pdf': '.pdf',
            'pptx_to_pdf':  '.pdf',
        }
        out_ext = ext_map.get(conversion_type, '.out')
        original_name   = os.path.splitext(f.name)[0]
        output_filename = f'{original_name}_converted{out_ext}'
        tmp_in  = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(f.name)[1])
        tmp_out = tempfile.NamedTemporaryFile(delete=False, suffix=out_ext)
        try:
            for chunk in f.chunks():
                tmp_in.write(chunk)
            tmp_in.close()
            tmp_out.close()
            convert_file(tmp_in.name, conversion_type, tmp_out.name)
            return FileResponse(open(tmp_out.name, 'rb'), as_attachment=True, filename=output_filename)
        except Exception as e:
            messages.error(request, f'Conversion failed: {str(e)}')
            return redirect('convert')
        finally:
            try:
                os.unlink(tmp_in.name)
            except:
                pass
    messages.error(request, 'Please upload a file.')
    return redirect('convert')

# ── COMPRESS ─────────────────────────────────────────────────────
def compress(request):
    return render(request, 'core/compress.html')

def do_compress(request):
    if request.method == 'POST' and request.FILES.get('file'):
        f = request.FILES['file']
        if not file_size_ok(f):
            messages.error(request, 'File too large. Maximum size is 20MB.')
            return redirect('compress')
        ext = os.path.splitext(f.name)[1].lower()
        tmp_in  = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        tmp_out = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        try:
            for chunk in f.chunks():
                tmp_in.write(chunk)
            tmp_in.close()
            tmp_out.close()
            if ext == '.pdf':
                compress_pdf(tmp_in.name, tmp_out.name)
            elif ext in ['.jpg', '.jpeg', '.png']:
                compress_image(tmp_in.name, tmp_out.name)
            else:
                messages.error(request, 'Only PDF, JPG and PNG files can be compressed.')
                return redirect('compress')
            output_filename = os.path.splitext(f.name)[0] + '_compressed' + ext
            return FileResponse(open(tmp_out.name, 'rb'), as_attachment=True, filename=output_filename)
        except Exception as e:
            messages.error(request, f'Compression failed: {str(e)}')
            return redirect('compress')
        finally:
            try:
                os.unlink(tmp_in.name)
            except:
                pass
    messages.error(request, 'Please upload a file.')
    return redirect('compress')

# ── MERGE ────────────────────────────────────────────────────────
def merge(request):
    return render(request, 'core/merge.html')

def do_merge(request):
    if request.method == 'POST':
        files = request.FILES.getlist('files')
        if len(files) < 2:
            messages.error(request, 'Please upload at least 2 PDF files to merge.')
            return redirect('merge')
        tmp_inputs = []
        tmp_out = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        tmp_out.close()
        try:
            for f in files:
                if not file_size_ok(f):
                    messages.error(request, f'File "{f.name}" is too large. Maximum size is 20MB.')
                    return redirect('merge')
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                for chunk in f.chunks():
                    tmp.write(chunk)
                tmp.close()
                tmp_inputs.append(tmp.name)
            merge_pdfs(tmp_inputs, tmp_out.name)
            return FileResponse(open(tmp_out.name, 'rb'), as_attachment=True, filename='merged.pdf')
        except Exception as e:
            messages.error(request, f'Merge failed: {str(e)}')
            return redirect('merge')
        finally:
            for path in tmp_inputs:
                try:
                    os.unlink(path)
                except:
                    pass
    return redirect('merge')

# ── SPLIT ────────────────────────────────────────────────────────
def split(request):
    return render(request, 'core/split.html')

def do_split(request):
    if request.method == 'POST' and request.FILES.get('file'):
        f = request.FILES['file']
        if not file_size_ok(f):
            messages.error(request, 'File too large. Maximum size is 20MB.')
            return redirect('split')
        tmp_in  = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        tmp_dir = tempfile.mkdtemp()
        try:
            for chunk in f.chunks():
                tmp_in.write(chunk)
            tmp_in.close()
            output_files = split_pdf(tmp_in.name, tmp_dir)
            zip_path = os.path.join(tmp_dir, 'split_pages.zip')
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for page_file in output_files:
                    zipf.write(page_file, os.path.basename(page_file))
            return FileResponse(open(zip_path, 'rb'), as_attachment=True, filename='split_pages.zip')
        except Exception as e:
            messages.error(request, f'Split failed: {str(e)}')
            return redirect('split')
        finally:
            try:
                os.unlink(tmp_in.name)
            except:
                pass
    messages.error(request, 'Please upload a PDF file.')
    return redirect('split')

# ── SUMMARIZE ────────────────────────────────────────────────────
def summarize(request):
    return render(request, 'core/summarize.html')

def do_summarize(request):
    if request.method == 'POST' and request.FILES.get('file'):
        f   = request.FILES['file']
        ext = os.path.splitext(f.name)[1].lower()
        if not file_size_ok(f):
            messages.error(request, 'File too large. Maximum size is 20MB.')
            return redirect('summarize')
        tmp_in = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        try:
            for chunk in f.chunks():
                tmp_in.write(chunk)
            tmp_in.close()
            num_sentences = int(request.POST.get('num_sentences', 10))
            summaries = ai_summarize(tmp_in.name, num_sentences)
            return render(request, 'core/summarize.html', {
                'summaries': summaries,
                'filename': f.name
            })
        except Exception as e:
            messages.error(request, f'Summarization failed: {str(e)}')
            return redirect('summarize')
        finally:
            try:
                os.unlink(tmp_in.name)
            except:
                pass
    messages.error(request, 'Please upload a file.')
    return redirect('summarize')

# ── CUSTOM 404 ───────────────────────────────────────────────────
def custom_404(request, exception):
    return render(request, 'core/404.html', status=404)