import os
import subprocess
from pathlib import Path
import threading
import queue

# --- CONFIGURAZIONE ---
# Costante per gestire il numero di thread worker da avviare
NUM_THREADS = 5  # Modifica questo valore per usare più o meno core della CPU

# Configura le cartelle di input e output
INPUT_FOLDER = Path(r"F:\prove\in")
OUTPUT_FOLDER = Path(r"F:\prove\out2")

# --- FUNZIONE WORKER ESEGUITA DA OGNI THREAD ---
def process_file(q: queue.Queue):
    """
    Questa funzione viene eseguita da ogni thread.
    Continua a prelevare file dalla coda (q) e a processarli
    finché la coda non è vuota.
    """
    while True:
        try:
            # Preleva un percorso di file dalla coda.
            # Se la coda è vuota, get() attenderà finché non ci sarà un elemento.
            file_path = q.get()

            # Condizione di uscita: se riceviamo None, il thread deve terminare.
            if file_path is None:
                break

            thread_name = threading.current_thread().name
            print(f"[{thread_name}] Inizio elaborazione di: {file_path.name}")

            # Calcola il percorso relativo rispetto alla cartella di input
            rel_path = file_path.relative_to(INPUT_FOLDER)

            # Ottieni la directory di output relativa
            rel_dir = OUTPUT_FOLDER / rel_path.parent

            # Crea la struttura della cartella di output se necessario
            # (è thread-safe grazie a exist_ok=True)
            rel_dir.mkdir(parents=True, exist_ok=True)

            # Percorso completo del file di output
            output_file = rel_dir / f"{file_path.stem}.mp4"

            # Verifica se il file di output esiste già
            if output_file.exists():
                print(f"[{thread_name}] Il file di destinazione esiste già: {output_file}. Salto.")
            else:
                # Controlla se il file è codificato in H.264
                ffprobe_command = f'ffprobe -v quiet -select_streams v:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 "{file_path}"'
                result = subprocess.run(ffprobe_command, capture_output=True, text=True, shell=True, encoding='utf-8', errors='ignore')

                if 'h264' in result.stdout.lower():
                    print(f"[{thread_name}] {file_path.name} è H.264. Converto in HEVC...")
                    ffmpeg_command = f'ffmpeg -y -i "{file_path}" -c:v hevc_amf -qp 6 -rc qvbr -c:a copy "{output_file}"'
                    subprocess.run(ffmpeg_command, shell=True, check=True, capture_output=True) # Aggiunto capture_output per sopprimere l'output di ffmpeg
                    print(f"[{thread_name}] Conversione completata: {output_file}")
                else:
                    print(f"[{thread_name}] {file_path.name} non è H.264. Copio il file...")
                    # Usiamo il comando 'copy' che è specifico di Windows, attenzione alla portabilità
                    cp_cmd = f'copy "{file_path}" "{output_file}"'
                    subprocess.run(cp_cmd, shell=True, check=True, capture_output=True)

        except subprocess.CalledProcessError as e:
            print(f"[{thread_name}] ERRORE durante l'elaborazione di {file_path}: {e}")
            print(f"Output del comando: {e.stdout.decode('utf-8', errors='ignore')}")
            print(f"Errore del comando: {e.stderr.decode('utf-8', errors='ignore')}")
        except Exception as e:
            print(f"[{thread_name}] Si è verificato un errore imprevisto: {e}")
        finally:
            # Segnala alla coda che il task prelevato è stato completato.
            # Questo è fondamentale per far funzionare q.join().
            q.task_done()

# --- FUNZIONE PRINCIPALE (ORCHESTRATORE) ---
def main():
    # Crea la cartella di output principale se non esiste
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
    
    # 1. Crea la coda per i task
    task_queue = queue.Queue()

    # 2. Popola la coda (PRODUTTORE)
    # Raccogliamo prima tutti i percorsi dei file per avere un'idea del lavoro totale.
    print("Scansione dei file da elaborare in corso...")
    file_list = list(INPUT_FOLDER.rglob("*.*"))
    if not file_list:
        print("Nessun file trovato nella cartella di input. Uscita.")
        return

    print(f"Trovati {len(file_list)} file. Aggiungo i task alla coda.")
    for file_path in file_list:
        task_queue.put(file_path)

    # 3. Crea e avvia i thread worker (CONSUMATORI)
    threads = []
    print(f"Avvio di {NUM_THREADS} thread worker...")
    for i in range(NUM_THREADS):
        thread = threading.Thread(
            target=process_file,
            args=(task_queue,),
            name=f"Worker-{i+1}" # Diamo un nome al thread per un logging più chiaro
        )
        thread.start()
        threads.append(thread)

    # 4. Attendi che tutti gli elementi nella coda siano stati processati
    # q.join() si sblocca solo quando per ogni elemento inserito con put()
    # è stata chiamata una q.task_done()
    task_queue.join()

    # 5. Ferma i worker
    # Una volta che tutti i task sono completati, inviamo un segnale 'None'
    # per ogni thread per dirgli di terminare.
    for _ in range(NUM_THREADS):
        task_queue.put(None)

    # 6. Attendi la terminazione effettiva di tutti i thread
    for thread in threads:
        thread.join()

    print("\nOperazione completata per tutti i file.")

if __name__ == "__main__":
    main()