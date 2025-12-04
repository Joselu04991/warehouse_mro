import schedule
import time
from utils.pdf_report import create_pdf_reporte

def tarea_diaria():
    print("Enviando reporte diario…")
    create_pdf_reporte()

def run_scheduler():
    schedule.every().day.at("07:00").do(tarea_diaria)

    while True:
        schedule.run_pending()
        time.sleep(1)
