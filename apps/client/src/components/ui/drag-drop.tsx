"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { Upload, AlertCircle, Paperclip, FileUp, XIcon, FileSearch } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "./button";
import { Badge } from "./badge";

// Tipos para o componente de drag & drop
export interface DragDropProps {
  value: File | File[] | null;
  onChange: (file: File | File[] | null) => void;
  accept?: string[];
  maxSizeMb?: number;
  className?: string;
  disabled?: boolean;
  error?: string;
  multiple?: boolean;
}

// Estados do componente
export type DragDropState =
  | "idle"
  | "dragging"
  | "uploading"
  | "success"
  | "error";

export function DragDrop({
  value,
  onChange,
  accept,
  maxSizeMb = 10,
  className,
  disabled = false,
  error: externalError,
  multiple = false,
}: DragDropProps) {
  const [state, setState] = useState<DragDropState>("idle");
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string>("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Captura os arquivos iniciais (que vieram com o componente na montagem ou via props/contexto)
  const initialFileKeysRef = useRef<Set<string>>(new Set());
  const hasInitialized = useRef(false);
  const userAddedFilesRef = useRef<Set<string>>(new Set());

  // Inicializa o Set de arquivos iniciais no primeiro render
  if (!hasInitialized.current) {
    const initialFiles = value 
      ? (Array.isArray(value) ? value : [value])
      : [];
    initialFileKeysRef.current = new Set(
      initialFiles.map((f) => `${f.name}_${f.size}_${f.lastModified}`)
    );
    hasInitialized.current = true;
  }

  // Monitora mudanças no value para capturar arquivos que vêm "de fora" (contexto/props)
  useEffect(() => {
    if (value) {
      const currentFiles = Array.isArray(value) ? value : [value];
      const currentKeys = currentFiles.map((f) => `${f.name}_${f.size}_${f.lastModified}`);
      
      // Para cada arquivo atual, se não foi adicionado pelo usuário, marca como inicial
      currentKeys.forEach((key) => {
        if (!userAddedFilesRef.current.has(key)) {
          initialFileKeysRef.current.add(key);
        }
      });
    }
  }, [value]);

  useEffect(() => {
    const hasFiles = Array.isArray(value) ? value.length > 0 : !!value;
    setState(hasFiles ? "success" : "idle");
  }, [value]);

  const isInitialFile = (file: File) => {
    const key = `${file.name}_${file.size}_${file.lastModified}`;
    return initialFileKeysRef.current.has(key);
  };

  // Função para validar arquivo
  const validateFile = useCallback(
    (file: File): string | null => {
      const defaultAccept = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        ".pdf",
        ".doc",
        ".docx",
        ".txt",
      ];
      const list = (accept?.length ? accept : defaultAccept).map((a) =>
        a.toLowerCase()
      );
      const allowedTypes = list.filter((a) => a.includes("/"));
      const allowedExts = list.filter((a) => a.startsWith("."));

      if (file.size > (maxSizeMb ?? 10) * 1024 * 1024) {
        return `Arquivo deve ter no máximo ${maxSizeMb}MB`;
      }

      const fileExtension =
        "." + (file.name.split(".").pop() || "").toLowerCase();
      const typeOk =
        !allowedTypes.length || allowedTypes.includes(file.type.toLowerCase());
      const extOk = !allowedExts.length || allowedExts.includes(fileExtension);
      if (!typeOk && !extOk) {
        return "Apenas arquivos nos formatos permitidos";
      }

      if (!file.name.trim()) {
        return "Nome do arquivo é obrigatório";
      }

      return null;
    },
    [accept, maxSizeMb]
  );

  const fileKey = (f: File) => `${f.name}_${f.size}_${f.lastModified}`;

  const mergeFiles = (current: File[], incoming: File[]) => {
    const map = new Map<string, File>();
    current.forEach((f) => map.set(fileKey(f), f));
    incoming.forEach((f) => map.set(fileKey(f), f));
    return Array.from(map.values());
  };

  // Função para processar arquivo selecionado
  const handleFilesSelect = useCallback(
    (incoming: File[]) => {
      if (!incoming.length) {
        setError("Nenhum arquivo selecionado");
        setState("error");
        return;
      }

      const validations = incoming.map((f) => ({
        file: f,
        err: validateFile(f),
      }));
      const valid = validations.filter((v) => !v.err).map((v) => v.file);
      const firstError = validations.find((v) => v.err)?.err || "";

      // Marca os arquivos válidos como "adicionados pelo usuário"
      valid.forEach((f) => {
        const key = fileKey(f);
        userAddedFilesRef.current.add(key);
      });

      if (multiple) {
        const current = Array.isArray(value) ? value : value ? [value] : [];
        const merged = mergeFiles(current, valid);

        if (!merged.length) {
          setError(firstError || "Arquivos inválidos");
          setState("error");
          return;
        }

        setError(
          firstError ? "Alguns arquivos foram ignorados por inválidos." : ""
        );
        setState("success");
        onChange(merged);
        return;
      }

      const first = valid[0];
      if (!first) {
        setError(firstError || "Arquivo inválido");
        setState("error");
        return;
      }

      setError("");
      setState("success");
      onChange(first);
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [multiple, onChange, validateFile, value]
  );

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDragIn = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer?.items && e.dataTransfer.items.length > 0) {
      setDragActive(true);
    }
  }, []);

  const handleDragOut = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
    const x = e.clientX;
    const y = e.clientY;

    if (x < rect.left || x >= rect.right || y < rect.top || y >= rect.bottom) {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragActive(false);
      setError("");

      if (e.dataTransfer?.files && e.dataTransfer.files.length > 0) {
        const files = Array.from(e.dataTransfer.files);
        handleFilesSelect(multiple ? files : [files[0]]);
        e.dataTransfer.clearData();
      }
    },
    [handleFilesSelect, multiple]
  );

  const handleFileInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files ? Array.from(e.target.files) : [];
      if (files.length) {
        handleFilesSelect(multiple ? files : [files[0]]);
      }
    },
    [handleFilesSelect, multiple]
  );

  // Handler para remover arquivo
  const handleRemoveFile = useCallback(() => {
    onChange(null);
    setState("idle");
    setError("");
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }, [onChange]);

  const handleRemoveFileAt = useCallback(
    (index: number) => {
      if (!Array.isArray(value)) return;
      const next = value.filter((_, i) => i !== index);
      onChange(next);
      setState(next.length ? "success" : "idle");
      setError("");
      if (next.length === 0 && fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    },
    [onChange, value]
  );

  // Handler para abrir seletor de arquivo
  const handleClick = useCallback(() => {
    if (!disabled) {
      fileInputRef.current?.click();
    }
  }, [disabled]);

  // Handler para teclado (acessibilidade)
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        handleClick();
      }
    },
    [handleClick]
  );

  return (
    <div className={cn("w-full", className)}>
      {/* Input de arquivo oculto */}
      <input
        ref={fileInputRef}
        type="file"
        className="hidden"
        accept={(accept?.length
          ? accept
          : [".pdf", ".doc", ".docx", ".txt"]
        ).join(",")}
        onChange={handleFileInputChange}
        disabled={disabled}
        multiple={multiple}
      />

      {/* Área de drag & drop */}
      <div
        className={cn(
          "relative border-2 border-dashed border-gray-300 rounded-lg p-6 text-center transition-all duration-200 cursor-default",
          dragActive && "border-primary bg-primary/5",
          state === "error" && "border-destructive bg-destructive/5",
          state === "success" && "border-brand-green bg-brand-green/5",
          disabled && "opacity-50 cursor-not-allowed"
        )}
        onDragEnter={handleDragIn}
        onDragLeave={handleDragOut}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onKeyDown={handleKeyDown}
        role="button"
        aria-label="Arraste o arquivo para fazer upload"
        aria-describedby={error ? "file-error" : undefined}
      >
        <div className="space-y-3 flex flex-col items-center justify-center">
          <Upload className="mx-auto h-5 w-5 text-gray-400" />
          <div className="space-y-1 flex flex-col items-center justify-center">
            <p className="text-sm font-medium text-black">
              Arraste o arquivo para fazer upload
            </p>
            <p className="text-xs text-muted-foreground">OU</p>

            <Button
              variant="outline"
              className="align-center"
              size="sm"
              type="button"
              onClick={handleClick}
            >
              <Paperclip className="h-4 w-4 mr-2" />
              Anexar arquivo
            </Button>
          </div>
        </div>
      </div>

      {value && !Array.isArray(value) && (() => {
        const isInitial = isInitialFile(value);
        return (
          <div className="flex items-center space-x-2 mt-2 text-xs">
            <Badge
              variant="outline"
              className="rounded-full py-1 px-2 font-medium flex items-center space-x-2 border-brand-gray-300"
            >
              {isInitial ? (
                <FileSearch className="h-3 w-3 text-brand-accent" />
              ) : (
                <FileUp className="h-3 w-3 text-gray-900" />
              )}
              <span className={isInitial ? 'text-brand-accent' : 'text-gray-900'}>
                {value.name}
              </span>
              <XIcon
                onClick={handleRemoveFile}
                className="h-4 w-4 cursor-pointer text-gray-900"
              />
            </Badge>
          </div>
        );
      })()}

      {Array.isArray(value) && value.length > 0 && (
        <div className="flex flex-wrap gap-2 mt-2 text-xs">
          {value.map((file, idx) => {
            const isInitial = isInitialFile(file);
            return (
              <Badge
                key={`${file.name}-${file.size}-${file.lastModified}`}
                variant="outline"
                className="rounded-full py-1 px-2 font-medium flex items-center space-x-2 border-brand-gray-300"
              >
                {isInitial ? (
                  <FileSearch className="h-3 w-3 text-brand-accent" />
                ) : (
                  <FileUp className="h-3 w-3 text-gray-900" />
                )}
                <span className={cn(
                  "truncate max-w-[200px]",
                  isInitial ? 'text-brand-accent' : 'text-gray-900'
                )}>
                  {file.name}
                </span>
                <XIcon
                  onClick={() => handleRemoveFileAt(idx)}
                  className="h-4 w-4 cursor-pointer text-gray-900"
                  aria-label={`Remover ${file.name}`}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ")
                      handleRemoveFileAt(idx);
                  }}
                />
              </Badge>
            );
          })}
        </div>
      )}

      {/* Mensagem de erro */}
      {(externalError || error) && (
        <div
          id="file-error"
          className="flex items-center space-x-2 mt-2 text-sm text-destructive"
          role="alert"
        >
          <AlertCircle className="h-4 w-4" />
          <span>{externalError || error}</span>
        </div>
      )}
    </div>
  );
}
