# devsecops-pipeline

Progetto dimostrativo: una piccola API di note in Flask, con una pipeline GitHub Actions che controlla la sicurezza a ogni push.

## La pipeline

| Controllo   | Strumento        | Cosa cerca                                                    |
|-------------|------------------|---------------------------------------------------------------|
| Test        | pytest           | che l'app funzioni, incluso un test contro la SQL injection   |
| SAST        | Bandit, Semgrep  | codice pericoloso: SQL costruito a mano, `shell=True`, debug  |
| Segreti     | Gitleaks         | password e chiavi nel codice e in tutta la storia dei commit  |
| Dipendenze  | pip-audit        | librerie con vulnerabilità note (CVE)                         |
| SBOM        | CycloneDX        | elenco dei componenti, scaricabile come artifact              |

## I due rami

- **`main`**: versione sicura. Tutti i controlli passano.
- **`demo/vulnerable`**: stessa app con vulnerabilità inserite apposta. La pipeline deve diventare rossa.

| Vulnerabilità inserita            | Chi la trova            |
|-----------------------------------|-------------------------|
| SQL injection nella ricerca       | pytest, Bandit, Semgrep |
| Comando di sistema con `shell=True` | Bandit, Semgrep       |
| Flask con `debug=True`            | Semgrep                 |
| Chiave AWS finta in `app/config.py` | Gitleaks              |
| Flask 2.2.4, Werkzeug 2.2.2, Jinja2 3.1.2, requests 2.28.1 | pip-audit |

Per vedere la differenza: apri una pull request da `demo/vulnerable` verso `main` (senza unirla) e guarda la scheda **Checks**.

## Avvio in locale

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest
python run.py   # http://127.0.0.1:5000/health
```

La chiave AWS nel ramo vulnerabile è inventata: non dà accesso a nulla.
