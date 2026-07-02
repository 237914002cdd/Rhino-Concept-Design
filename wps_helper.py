"""
WPS COM 自动化助手 — 简历工作流专用
依赖: pip install pywin32

用法:
  from wps_helper import open_doc, docx_to_pdf, pdf_to_docx, save_and_close, quit_all

  app, doc = open_doc(r'path/to/resume.docx')
  # ... 操作 doc
  save_and_close(doc, r'path/to/output.docx')
  quit_all()
"""
import win32com.client
import pythoncom
import os
from pathlib import Path
from contextlib import contextmanager

_dispatch_cache = {}
_com_initialized = False

def _ensure_com():
    global _com_initialized
    if not _com_initialized:
        pythoncom.CoInitialize()
        _com_initialized = True

def _get_app(progid, visible=True):
    _ensure_com()
    key = (progid, os.getpid())
    if key not in _dispatch_cache:
        _dispatch_cache[key] = win32com.client.Dispatch(progid)
    _dispatch_cache[key].Visible = visible
    return _dispatch_cache[key]

def writer(visible=True):
    return _get_app('Kwps.Application', visible)

def spreadsheets(visible=True):
    return _get_app('Ket.Application', visible)

def open_doc(path, visible=False):
    """用 WPS Writer 打开文档，返回 (app, doc)"""
    path = str(Path(path).resolve())
    if not os.path.exists(path):
        raise FileNotFoundError(f'文件不存在: {path}')
    app = writer(visible)
    doc = app.Documents.Open(path)
    return app, doc

def save_and_close(doc, path=None):
    """保存并关闭文档。path=None 则覆盖原文件。"""
    if path:
        path = str(Path(path).resolve())
        doc.SaveAs2(path)
    else:
        doc.Save()
    doc.Close()

def docx_to_pdf(docx_path, pdf_path=None):
    """将 .docx 导出为 .pdf"""
    docx_path = str(Path(docx_path).resolve())
    if pdf_path is None:
        pdf_path = docx_path.rsplit('.', 1)[0] + '.pdf'
    pdf_path = str(Path(pdf_path).resolve())

    app, doc = open_doc(docx_path, visible=False)
    try:
        doc.SaveAs2(pdf_path, 17)  # wdFormatPDF = 17
        return pdf_path
    finally:
        try: doc.Close()
        except: pass
        app.Quit()
        _dispatch_cache.clear()

def pdf_to_docx(pdf_path, docx_path=None):
    """将 .pdf 另存为 .docx（WPS 的 PDF 转 Word 功能）"""
    pdf_path = str(Path(pdf_path).resolve())
    if docx_path is None:
        docx_path = pdf_path.rsplit('.', 1)[0] + '.docx'
    docx_path = str(Path(docx_path).resolve())

    app, doc = open_doc(pdf_path, visible=False)
    try:
        doc.SaveAs2(docx_path, 13)  # wdFormatDocumentDefault = 16? Try 13 for PDF re-save
        return docx_path
    finally:
        try: doc.Close()
        except: pass
        app.Quit()
        _dispatch_cache.clear()

def batch_pdf_export(folder, pattern='*.docx'):
    """批量导出目录下所有匹配的 .docx 为 .pdf"""
    folder = Path(folder)
    files = sorted(folder.glob(pattern))
    results = []
    for f in files:
        pdf = docx_to_pdf(str(f))
        results.append((f.name, pdf))
    return results

def get_wps_version():
    """获取 WPS 版本号"""
    app = writer(visible=False)
    ver = app.Version
    app.Quit()
    return f'WPS Writer v{ver}'

def view(path):
    """在 WPS 中打开文档（可见模式）"""
    app, doc = open_doc(path, visible=True)
    return app, doc

def quit_all():
    _ensure_com()
    for key in list(_dispatch_cache.keys()):
        try:
            _dispatch_cache[key].Quit()
        except:
            pass
    _dispatch_cache.clear()

if __name__ == '__main__':
    # 快速测试
    versions = []
    for progid, name in [
        ('Kwps.Application', 'Writer'),
        ('Ket.Application', 'Spreadsheets'),
        ('KWPP.Application', 'Presentation'),
    ]:
        app = win32com.client.Dispatch(progid)
        versions.append(f'{name} v{app.Version}')
        app.Quit()
    print('WPS 连接测试通过:', ' | '.join(versions))
