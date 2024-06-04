import nfc
import time
from datetime import datetime
import pandas as pd
import tkinter as tk
from tkinter import messagebox

# Dati degli utenti
users = {}

# Funzione per rilevare l'ID della tessera NFC
def on_connect(tag):
    nfc_id = tag.identifier.hex()
    print(f"Tessera rilevata: {nfc_id}")

    # Ottenere l'ora attuale
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if nfc_id in users:
        last_action = users[nfc_id][-1]['action']
        if last_action == 'in':
            action = 'out'
            last_time = datetime.strptime(users[nfc_id][-1]['time'], "%Y-%m-%d %H:%M:%S")
            active_time = (datetime.now() - last_time).total_seconds()
            users[nfc_id][-1]['active_time'] = active_time
            messagebox.showinfo("Uscita", f"Tessera {nfc_id}\nUscita alle {current_time}\nTempo attivo: {active_time / 60:.2f} minuti")
        else:
            action = 'in'
            messagebox.showinfo("Ingresso", f"Tessera {nfc_id}\nIngresso alle {current_time}")
    else:
        action = 'in'
        users[nfc_id] = []

    users[nfc_id].append({'time': current_time, 'action': action, 'active_time': 0})
    update_user_list()
    save_to_excel()
    return True

# Aggiornare la lista degli utenti nella GUI
def update_user_list():
    user_list.delete(0, tk.END)
    for user_id, logs in users.items():
        user_list.insert(tk.END, f"Tessera {user_id}:")
        total_time = sum(log['active_time'] for log in logs) / 60  # Convert to minutes
        user_list.insert(tk.END, f"  Tempo totale attivo: {total_time:.2f} minuti")
        for log in logs:
            user_list.insert(tk.END, f"  {log['action']} - {log['time']}")

# Salvare i dati in un file Excel
def save_to_excel():
    data = []
    for user_id, logs in users.items():
        for log in logs:
            data.append({'Tessera': user_id, 'Azione': log['action'], 'Ora': log['time'], 'Tempo Attivo (s)': log['active_time']})
    df = pd.DataFrame(data)
    df.to_excel('accessi_nfc.xlsx', index=False)

# Impostare il lettore NFC
def start_nfc_reader():
    try:
        clf = nfc.ContactlessFrontend('usb')  # Prova con 'usb'
    except Exception as e:
        print(f"Errore con backend 'usb': {e}")
        try:
            clf = nfc.ContactlessFrontend('libusbK')  # Prova con 'libusbK'
        except Exception as e:
            print(f"Errore con backend 'libusbK': {e}")
            messagebox.showerror("Errore", "Nessun lettore NFC supportato trovato.")
            return

    try:
        while True:
            # Attendere una tessera NFC
            clf.connect(rdwr={'on-connect': on_connect})
            time.sleep(1)  # Piccola pausa per evitare doppie letture immediate
    except KeyboardInterrupt:
        print("Interruzione del programma.")
    finally:
        clf.close()

# Creare l'interfaccia grafica
root = tk.Tk()
root.title("Sistema di Conteggio Accessi NFC")

frame = tk.Frame(root)
frame.pack(pady=20)

title = tk.Label(frame, text="Lettura del Badge NFC", font=("Helvetica", 16))
title.pack(pady=10)

user_list = tk.Listbox(frame, width=50, height=15)
user_list.pack(pady=10)

# Avviare il lettore NFC in un thread separato
import threading
nfc_thread = threading.Thread(target=start_nfc_reader, daemon=True)
nfc_thread.start()

root.mainloop()
