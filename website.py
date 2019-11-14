from app import app, cli
from app.models import UN, NATO, WorldBank


@app.shell_context_processor
def make_shell_context():
    return {
        'UN': UN,
        'NATO': NATO,
        'WorldBank': WorldBank
    }
