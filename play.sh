#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Asegurar servicio PostgreSQL
if ! pg_isready -q 2>/dev/null; then
    echo -e "${YELLOW}Iniciando servicio PostgreSQL...${NC}"
    sudo service postgresql start 2>/dev/null || true
fi

# Activar entorno virtual
if [ -f "$DIR/.venv/bin/activate" ]; then
    source "$DIR/.venv/bin/activate"
else
    echo -e "${RED}ERROR: No se encontro el entorno virtual en $DIR/.venv${NC}"
    exit 1
fi

COMMAND="${1:-all}"
shift || true

case "$COMMAND" in
    all|"")
        echo -e "${CYAN}============================================================${NC}"
        echo -e "${GREEN}  SGAF - Sistema de Gestion de Activos Fijos                ${NC}"
        echo -e "${CYAN}============================================================${NC}"
        echo -e "  Backend API:  ${GREEN}http://localhost:8000/docs${NC}"
        echo -e "  Frontend Web: ${GREEN}http://localhost:3000${NC}"
        echo -e "${YELLOW}  Presiona Ctrl+C para detener ambos servicios.${NC}"
        echo -e "${CYAN}============================================================${NC}\n"

        trap 'echo -e "\n${RED}Deteniendo servicios...${NC}"; kill 0' SIGINT SIGTERM EXIT

        uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
        sleep 1.5

        cd "$DIR/frontend"
        exec npm run dev
        ;;

    backend|api)
        echo -e "${GREEN}Iniciando Backend FastAPI (puerto 8000)...${NC}"
        exec uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
        ;;

    frontend|web)
        echo -e "${GREEN}Iniciando Frontend Next.js (puerto 3000)...${NC}"
        cd "$DIR/frontend"
        exec npm run dev
        ;;

    test|tests)
        exec pytest "$DIR/tests" -v "$@"
        ;;

    cli)
        exec python "$DIR/cli.py" "$@"
        ;;

    db)
        exec python "$DIR/cli.py" db "$@"
        ;;

    ingestar)
        exec python "$DIR/cli.py" ingestar-factura "$@"
        ;;

    cierre|depreciacion)
        exec python "$DIR/cli.py" depreciacion cerrar-mes "$@"
        ;;

    baja)
        exec python "$DIR/cli.py" activo reportar-baja "$@"
        ;;

    help|--help|-h)
        echo -e "${CYAN}Uso: ./play.sh [comando]${NC}"
        echo -e "  all                  Inicia Backend + Frontend juntos (por defecto)"
        echo -e "  backend              Inicia solo FastAPI (puerto 8000)"
        echo -e "  frontend             Inicia solo Next.js (puerto 3000)"
        echo -e "  test                 Ejecuta las pruebas con pytest"
        echo -e "  db ping              Verifica conexion a PostgreSQL"
        echo -e "  ingestar [args]      Ingesta de factura por IA / Mock"
        echo -e "  cierre [args]        Cierre contable mensual de depreciacion"
        echo -e "  baja [args]          Liquidacion de baja patrimonial"
        echo -e "  cli [args...]        Acceso directo a la consola cli.py"
        ;;

    *)
        echo -e "${RED}Comando no reconocido: '$COMMAND'${NC}"
        echo -e "Ejecuta ./play.sh help para ver los comandos disponibles."
        exit 1
        ;;
esac