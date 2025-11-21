import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { cn } from '@/lib/utils';
import { Download, Edit, Eye, FileText, Image, Trash2, Upload, X } from 'lucide-react';
import React, { useState } from 'react';

interface FileUploadProps {
    label: string;
    name: string;
    value?: File | null;
    onChange: (file: File | null) => void;
    onBlur?: () => void;
    accept?: string;
    maxSize?: number; // in MB
    required?: boolean;
    disabled?: boolean;
    error?: string;
    allowEdit?: boolean;
    downloadUrl?: string;
    previewUrl?: string;
    showPreview?: boolean;
    allowDelete?: boolean;
    onDelete?: () => void;
    className?: string;
    placeholder?: string;
    helpText?: string;
}

export function FileUpload({
    label,
    name,
    value,
    onChange,
    onBlur,
    accept = '.pdf,.jpg,.jpeg,.png,.doc,.docx',
    maxSize = 4, // 4MB default
    required = false,
    disabled = false,
    error,
    allowEdit = false,
    downloadUrl,
    previewUrl,
    showPreview = false,
    allowDelete = false,
    onDelete,
    className,
    placeholder = 'Pilih file...',
    helpText,
}: FileUploadProps) {
    const [isDragOver, setIsDragOver] = useState(false);
    const [showExistingFile, setShowExistingFile] = useState(true);
    const [isEditMode, setIsEditMode] = useState(false);
    const [localError, setLocalError] = useState('');

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0] || null;

        if (file) {
            // Validate file size
            if (file.size > maxSize * 1024 * 1024) {
                // You might want to show error through a toast or error prop
                console.error(`File size exceeds ${maxSize}MB limit`);
                setLocalError(`File size exceeds ${maxSize}MB limit`);
                return;
            }

            // Validate file type
            const allowedExtensions = accept.split(',').map((ext) => ext.trim().toLowerCase());
            const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();

            if (!allowedExtensions.includes(fileExtension)) {
                console.error(`File type not allowed. Allowed: ${accept}`);
                setLocalError(`File type not allowed. Allowed: ${accept}`);
                return;
            }
        }

        onChange(file);
    };

    const handleDragOver = (event: React.DragEvent) => {
        event.preventDefault();
        setIsDragOver(true);
    };

    const handleDragLeave = (event: React.DragEvent) => {
        event.preventDefault();
        setIsDragOver(false);
    };

    const handleDrop = (event: React.DragEvent) => {
        event.preventDefault();
        setIsDragOver(false);

        const file = event.dataTransfer.files[0];
        if (file) {
            // Create a synthetic event to reuse validation logic
            const syntheticEvent = {
                target: { files: [file] },
            } as unknown as React.ChangeEvent<HTMLInputElement>;

            handleFileChange(syntheticEvent);
        }
    };

    const formatFileSize = (bytes: number): string => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    const getFileIcon = (fileName: string) => {
        const extension = fileName.split('.').pop()?.toLowerCase();

        if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'].includes(extension || '')) {
            return <Image className="h-4 w-4" />;
        }

        return <FileText className="h-4 w-4" />;
    };

    const handleDeleteExisting = () => {
        if (onDelete) {
            onDelete();
        }
        setShowExistingFile(false);
    };

    const handleEditClick = () => {
        setIsEditMode(true);
        setShowExistingFile(false);
    };

    const handleCancelEdit = () => {
        setIsEditMode(false);
        setShowExistingFile(true);
        onChange(null); // Clear any selected file
        // Reset file input
        const fileInput = document.getElementById(name) as HTMLInputElement;
        if (fileInput) {
            fileInput.value = '';
        }
    };

    // Check if we have any existing file info (either from FileMetadata or URLs)
    const hasExistingFile = previewUrl || downloadUrl;

    // Determine if we should show the file input area
    const shouldShowInputArea = !hasExistingFile || isEditMode || !showExistingFile;

    // Get file display info (prioritize existingFile, fallback to URLs)
    const getFileDisplayInfo = () => {

        // Fallback: extract filename from URL
        const url = previewUrl || downloadUrl;
        if (url) {
            // Try to extract filename from URL
            const urlParts = url.split('/');
            const lastPart = urlParts[urlParts.length - 1];
            const fileName = lastPart.split('?')[0] || 'File';

            return {
                name: decodeURIComponent(fileName),
                size: null,
                hasMetadata: false,
            };
        }

        return null;
    };

    const fileInfo = getFileDisplayInfo();

    return (
        <div className={cn('space-y-2', className)}>
            <Label htmlFor={name}>
                {label}
                {required && <span className="ml-1 text-red-500">*</span>}
            </Label>

            {/* Show existing file if available and not in edit mode */}
            {hasExistingFile && showExistingFile && !isEditMode && fileInfo && (
                <div className="bg-muted/50 mb-3 rounded-lg border p-3">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                            {getFileIcon(fileInfo.name)}
                            <div className="text-sm">
                                <div className="font-medium">File saat ini:</div>
                                <div className="text-muted-foreground">{fileInfo.name}</div>
                                {fileInfo.size && <div className="text-muted-foreground text-xs">{formatFileSize(fileInfo.size)}</div>}
                                {!fileInfo.hasMetadata && <div className="text-muted-foreground text-xs italic">File tersedia</div>}
                            </div>
                        </div>

                        <div className="flex items-center space-x-2">
                            {downloadUrl && (
                                <Button type="button" variant="outline" size="sm" onClick={() => window.open(downloadUrl, '_blank')}>
                                    <Download className="mr-1 h-3 w-3" />
                                    Download
                                </Button>
                            )}

                            {previewUrl && showPreview && (
                                <Button type="button" variant="outline" size="sm" onClick={() => window.open(previewUrl, '_blank')}>
                                    <Eye className="mr-1 h-3 w-3" />
                                    Preview
                                </Button>
                            )}

                            {allowEdit && hasExistingFile && (
                                <Button type="button" variant="outline" size="sm" onClick={handleEditClick}>
                                    <Edit className="mr-1 h-3 w-3" />
                                    Edit
                                </Button>
                            )}

                            {allowDelete && onDelete && (
                                <Button type="button" variant="outline" size="sm" onClick={handleDeleteExisting}>
                                    <Trash2 className="mr-1 h-3 w-3" />
                                    Hapus
                                </Button>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* File input area - show when no existing file OR in edit mode */}
            {shouldShowInputArea && (
                <div className="space-y-3">
                    {/* Cancel button when in edit mode */}
                    {isEditMode && hasExistingFile && (
                        <div className="flex items-center justify-between rounded-lg border p-3 bg-secondary">
                            <div className="flex items-center space-x-2">
                                <Edit className="h-4 w-4" />
                                <p className="text-sm">Mode Edit: Pilih file baru untuk mengganti file yang ada</p>
                            </div>
                            <Button type="button" variant="outline" size="sm" onClick={handleCancelEdit}>
                                <X className="mr-1 h-3 w-3" />
                                Batal
                            </Button>
                        </div>
                    )}

                    <div
                        className={cn(
                            'rounded-lg border-2 border-dashed p-6 text-center transition-colors',
                            isDragOver ? 'border-primary bg-primary/5' : 'border-muted-foreground/25',
                            disabled ? 'cursor-not-allowed opacity-50' : 'hover:border-primary/50 cursor-pointer',
                            error ? 'border-red-500' : '',
                        )}
                        onDragOver={handleDragOver}
                        onDragLeave={handleDragLeave}
                        onDrop={handleDrop}
                        onClick={() => !disabled && document.getElementById(name)?.click()}
                    >
                        <Input
                            id={name}
                            name={name}
                            type="file"
                            accept={accept}
                            onChange={handleFileChange}
                            onBlur={onBlur}
                            disabled={disabled}
                            className="hidden"
                        />

                        <div className="space-y-2">
                            <Upload className="text-muted-foreground mx-auto h-8 w-8" />

                            {value ? (
                                <div className="space-y-1">
                                    <p className="text-sm font-medium">{value.name}</p>
                                    <p className="text-muted-foreground text-xs">{formatFileSize(value.size)}</p>
                                </div>
                            ) : (
                                <div className="space-y-1">
                                    <p className="text-sm font-medium">{placeholder}</p>
                                    <p className="text-muted-foreground text-xs">Drag & drop file atau klik untuk memilih</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Error message */}
            {error && <p className="text-xs text-red-500">{error}</p>}
            {!error && localError && <p className="text-xs text-red-500">{localError}</p>}

            {/* Help text */}
            {helpText && <p className="text-muted-foreground text-xs">{helpText}</p>}

            {/* File format and size info */}
            <div className="text-muted-foreground text-xs">
                Format yang didukung: {accept} • Maksimal {maxSize}MB
            </div>
        </div>
    );
}

export default FileUpload;
