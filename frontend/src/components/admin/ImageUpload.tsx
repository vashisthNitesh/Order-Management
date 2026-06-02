"use client";

import { useRef, useState } from "react";
import Image from "next/image";
import { Upload, X, ImageIcon } from "lucide-react";
import { getImageUrl } from "@/lib/utils";

interface ImageUploadProps {
  currentUrl?: string | null;
  onFileChange: (file: File | null) => void;
  label?: string;
  className?: string;
}

export function ImageUpload({
  currentUrl,
  onFileChange,
  label = "Item Image",
  className = "",
}: ImageUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);

  const handleSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setFileName(file.name);
    setPreview(URL.createObjectURL(file));
    onFileChange(file);
  };

  const handleRemove = () => {
    setPreview(null);
    setFileName(null);
    onFileChange(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  const displaySrc = preview || (currentUrl ? getImageUrl(currentUrl) : null);

  return (
    <div className={`space-y-1.5 ${className}`}>
      <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
        {label}
      </label>
      <div
        onClick={() => !displaySrc && inputRef.current?.click()}
        className={`relative rounded-2xl border-2 border-dashed transition-colors overflow-hidden ${
          displaySrc
            ? "border-transparent"
            : "border-gray-200 dark:border-gray-700 hover:border-emerald-400 cursor-pointer"
        } bg-gray-50 dark:bg-gray-800/50`}
      >
        {displaySrc ? (
          <div className="relative h-40 w-full">
            <Image
              src={displaySrc}
              alt="Preview"
              fill
              className="object-cover rounded-2xl"
              onError={(e) => {
                (e.target as HTMLImageElement).src = "/images/placeholder-food.jpg";
              }}
            />
            <div className="absolute inset-0 bg-black/30 rounded-2xl flex items-end p-3 gap-2">
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); inputRef.current?.click(); }}
                className="flex-1 flex items-center justify-center gap-1.5 bg-white/90 hover:bg-white text-gray-800 text-xs font-semibold rounded-xl py-2 transition-colors"
              >
                <Upload className="w-3.5 h-3.5" /> Change
              </button>
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); handleRemove(); }}
                className="w-9 h-9 bg-red-500/90 hover:bg-red-600 text-white rounded-xl flex items-center justify-center transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        ) : (
          <div className="h-32 flex flex-col items-center justify-center gap-2 text-gray-400">
            <div className="w-10 h-10 rounded-xl bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
              <ImageIcon className="w-5 h-5" />
            </div>
            <div className="text-center">
              <p className="text-xs font-medium">Click to upload image</p>
              <p className="text-[11px]">PNG, JPG up to 5MB</p>
            </div>
          </div>
        )}
      </div>
      {fileName && !preview?.startsWith("blob") ? null : fileName ? (
        <p className="text-xs text-emerald-600 font-medium truncate">✓ {fileName}</p>
      ) : null}
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handleSelect}
      />
    </div>
  );
}
