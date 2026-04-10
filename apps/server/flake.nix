{
  description = "AssessorAI development shell";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
  }:
    flake-utils.lib.eachDefaultSystem (system: let
      pkgs = import nixpkgs {
        inherit system;
      };
      lib = pkgs.lib;
      postgresql = pkgs.postgresql.withPackages (ps: [
        ps.pgvector
      ]);
      python = pkgs.python312.withPackages (ps: [
        ps.psycopg2
      ]);
    in {
      devShells.default = pkgs.mkShell {
        packages = with pkgs; [
          python
          uv
          pkg-config
          postgresql
          openssl
          libffi
          zlib
        ];

        LD_LIBRARY_PATH = lib.makeLibraryPath [
          pkgs.stdenv.cc.cc
          postgresql
          pkgs.openssl
          pkgs.libffi
          pkgs.zlib
        ];

        PKG_CONFIG_PATH = lib.makeSearchPath "lib/pkgconfig" [
          pkgs.openssl.dev
          postgresql
        ];

        shellHook = ''
          # shellHook roda em bash; exportar variaveis funciona para qualquer shell filho
          export VENV_DIR="$(pwd)/.venv"
          export PIP_DISABLE_PIP_VERSION_CHECK=1

          # Criar/recriar venv se necessario
          if [ ! -d "$VENV_DIR" ]; then
            python -m venv --system-site-packages "$VENV_DIR"
          fi

          if [ -f "$VENV_DIR/pyvenv.cfg" ] && ! ${pkgs.gnugrep}/bin/grep -q '^include-system-site-packages = true$' "$VENV_DIR/pyvenv.cfg"; then
            rm -rf "$VENV_DIR"
            python -m venv --system-site-packages "$VENV_DIR"
          fi

          shell_python_version="$(python -c 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")')"
          venv_python_version="$($VENV_DIR/bin/python -c 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")' 2>/dev/null || true)"
          if [ "$shell_python_version" != "$venv_python_version" ]; then
            rm -rf "$VENV_DIR"
            python -m venv --system-site-packages "$VENV_DIR"
          fi

          # Ativar venv via exportacao de variaveis (funciona em bash, zsh, fish)
          export VIRTUAL_ENV="$VENV_DIR"
          export PATH="$VENV_DIR/bin:$PATH"
          unset PYTHONHOME

          # Variaveis do Postgres local
          if [ -z "$ASSESSORAI_PGDATA" ]; then
            export ASSESSORAI_PGDATA="/tmp/assessorai-pg-$USER/data"
          fi
          if [ -z "$ASSESSORAI_PGLOG" ]; then
            export ASSESSORAI_PGLOG="/tmp/assessorai-pg-$USER/postgres.log"
          fi
          if [ -z "$ASSESSORAI_PGPORT" ]; then
            export ASSESSORAI_PGPORT="55432"
          fi
          if [ -z "$ASSESSORAI_PGHOST" ]; then
            export ASSESSORAI_PGHOST="127.0.0.1"
          fi
          if [ -z "$ASSESSORAI_PGADMIN_USER" ]; then
            export ASSESSORAI_PGADMIN_USER="$USER"
          fi
          if [ -z "$ASSESSORAI_PGSOCKET_DIR" ]; then
            export ASSESSORAI_PGSOCKET_DIR="/tmp/assessorai-pg-$USER"
          fi
          if [ -z "$DATABASE_URL" ]; then
            export DATABASE_URL="postgresql://postgres:password@$ASSESSORAI_PGHOST:$ASSESSORAI_PGPORT/assessorai"
          fi

          # Gravar helpers de pg em arquivo para ser carregado por qualquer shell
          _ASSESSORAI_HELPERS="$(pwd)/.nix-shell-helpers.sh"
          cat > "$_ASSESSORAI_HELPERS" << 'HELPERS'
assessorai_pg_up() {
  mkdir -p "$(dirname "$ASSESSORAI_PGDATA")"
  if [ ! -f "$ASSESSORAI_PGDATA/PG_VERSION" ]; then
    initdb --auth-local=trust --auth-host=trust -U "$ASSESSORAI_PGADMIN_USER" -D "$ASSESSORAI_PGDATA" >/dev/null
  fi
  if ! pg_ctl -D "$ASSESSORAI_PGDATA" status >/dev/null 2>&1; then
    mkdir -p "$ASSESSORAI_PGSOCKET_DIR"
    pg_ctl -D "$ASSESSORAI_PGDATA" -l "$ASSESSORAI_PGLOG" \
      -o "-h $ASSESSORAI_PGHOST -p $ASSESSORAI_PGPORT -k $ASSESSORAI_PGSOCKET_DIR" start >/dev/null
  fi
  if ! pg_isready -h "$ASSESSORAI_PGHOST" -p "$ASSESSORAI_PGPORT" >/dev/null 2>&1; then
    echo "Falha ao iniciar Postgres local; veja: $ASSESSORAI_PGLOG"
    return 1
  fi
  if [ "$(psql -h "$ASSESSORAI_PGHOST" -p "$ASSESSORAI_PGPORT" -U "$ASSESSORAI_PGADMIN_USER" -d postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname = 'postgres'")" != "1" ]; then
    psql -h "$ASSESSORAI_PGHOST" -p "$ASSESSORAI_PGPORT" -U "$ASSESSORAI_PGADMIN_USER" -d postgres \
      -c "CREATE ROLE postgres WITH LOGIN SUPERUSER PASSWORD 'password';" >/dev/null
  else
    psql -h "$ASSESSORAI_PGHOST" -p "$ASSESSORAI_PGPORT" -U "$ASSESSORAI_PGADMIN_USER" -d postgres \
      -c "ALTER USER postgres WITH PASSWORD 'password';" >/dev/null
  fi
  if [ "$(psql -h "$ASSESSORAI_PGHOST" -p "$ASSESSORAI_PGPORT" -U "$ASSESSORAI_PGADMIN_USER" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname = 'assessorai'")" != "1" ]; then
    createdb -h "$ASSESSORAI_PGHOST" -p "$ASSESSORAI_PGPORT" -U "$ASSESSORAI_PGADMIN_USER" assessorai
  fi
  psql -h "$ASSESSORAI_PGHOST" -p "$ASSESSORAI_PGPORT" -U postgres -d assessorai \
    -c "CREATE EXTENSION IF NOT EXISTS vector;" >/dev/null
  echo "Postgres pronto em $ASSESSORAI_PGHOST:$ASSESSORAI_PGPORT (db: assessorai, user: postgres)."
}

assessorai_pg_down() {
  if pg_ctl -D "$ASSESSORAI_PGDATA" status >/dev/null 2>&1; then
    pg_ctl -D "$ASSESSORAI_PGDATA" stop -m fast >/dev/null
    echo "Postgres local parado."
  else
    echo "Postgres local ja estava parado."
  fi
}

assessorai_pg_status() {
  pg_ctl -D "$ASSESSORAI_PGDATA" status
}
HELPERS

          # Carregar helpers no bash atual (shellHook)
          source "$_ASSESSORAI_HELPERS"

          # Instalar dependencias se necessario
          dep_hash="$(${pkgs.coreutils}/bin/sha256sum pyproject.toml uv.lock | ${pkgs.coreutils}/bin/sha256sum | ${pkgs.coreutils}/bin/cut -d' ' -f1)"
          stamp_file="$VENV_DIR/.requirements-hash"
          needs_install=0

          if ! "$VENV_DIR/bin/python" -c 'import fastapi, streamlit, psycopg2' >/dev/null 2>&1; then
            needs_install=1
          fi
          if ! "$VENV_DIR/bin/python" -c 'import assessorai' >/dev/null 2>&1; then
            needs_install=1
          fi
          if [ ! -f "$stamp_file" ] || [ "$(cat "$stamp_file")" != "$dep_hash" ]; then
            needs_install=1
          fi

          if [ "$needs_install" -eq 1 ]; then
            uv pip install --python "$VENV_DIR/bin/python" -e ".[client,test,dev]"
            printf '%s' "$dep_hash" > "$stamp_file"
          fi

          echo "AssessorAI dev shell ready (python: $("$VENV_DIR/bin/python" --version))."
          echo "Helpers disponiveis: assessorai_pg_up | assessorai_pg_down | assessorai_pg_status"
          echo "Se usar zsh/fish, rode: source .nix-shell-helpers.sh"
        '';
      };
    });
}
