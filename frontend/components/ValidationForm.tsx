'use client';

import { useState, useEffect } from 'react';
import { Save, AlertCircle, CheckCircle2, Loader2, Clock, ArrowRight, ThumbsUp } from 'lucide-react';
import { extractionAPI } from '@/lib/api/extraction.api';
import { ExtractionResult, Correction, FeedbackRecord } from '@/lib/types/extraction.types';
import { getConfidenceBadgeColor } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ConflictResolution, ConflictSummary } from '@/components/extraction/ConflictResolution';

interface ValidationFormProps {
  documentId: number | null;
  extractionResults: ExtractionResult | null;
  feedbackHistory?: FeedbackRecord[];
  onValidationComplete?: () => void;
}

export default function ValidationForm({ documentId, extractionResults, feedbackHistory = [], onValidationComplete }: ValidationFormProps) {
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [corrections, setCorrections] = useState<Correction[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [dismissedConflicts, setDismissedConflicts] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (extractionResults?.extracted_data) {
      setFormData(extractionResults.extracted_data);
      setCorrections([]);
      setError('');
      setSuccess('');
    }
  }, [extractionResults]);

  const handleConflictResolve = (fieldName: string, selectedValue: string) => {
    // Update form data with resolved value
    setFormData(prev => ({ ...prev, [fieldName]: selectedValue }));
    
    // Track as correction
    const originalValue = extractionResults?.extracted_data[fieldName] || '';
    if (selectedValue !== originalValue) {
      const existingCorrectionIndex = corrections.findIndex(c => c.field_name === fieldName);
      const correction: Correction = {
        field_name: fieldName,
        original_value: originalValue,
        corrected_value: selectedValue,
        confidence_score: extractionResults?.confidence_scores[fieldName]
      };
      
      if (existingCorrectionIndex >= 0) {
        setCorrections(prev => {
          const updated = [...prev];
          updated[existingCorrectionIndex] = correction;
          return updated;
        });
      } else {
        setCorrections(prev => [...prev, correction]);
      }
    }
  };
  
  const handleConflictDismiss = (fieldName: string) => {
    setDismissedConflicts(prev => new Set(prev).add(fieldName));
  };

  const handleFieldChange = (fieldName: string, newValue: string) => {
    setFormData(prev => ({ ...prev, [fieldName]: newValue }));
    
    // Track correction if value changed
    const originalValue = extractionResults?.extracted_data[fieldName] || '';
    if (newValue !== originalValue) {
      const existingCorrectionIndex = corrections.findIndex(c => c.field_name === fieldName);
      const correction: Correction = {
        field_name: fieldName,
        original_value: originalValue,
        corrected_value: newValue,
        confidence_score: extractionResults?.confidence_scores[fieldName]
      };
      
      if (existingCorrectionIndex >= 0) {
        setCorrections(prev => {
          const updated = [...prev];
          updated[existingCorrectionIndex] = correction;
          return updated;
        });
      } else {
        setCorrections(prev => [...prev, correction]);
      }
    } else {
      // Remove correction if value reverted to original
      setCorrections(prev => prev.filter(c => c.field_name !== fieldName));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!documentId) {
      setError('Document ID tidak ditemukan');
      return;
    }

    if (corrections.length === 0) {
      setError('Tidak ada koreksi yang perlu disimpan');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      // Convert corrections array to Record<string, string> format
      const correctionsMap: Record<string, string> = {};
      corrections.forEach(correction => {
        correctionsMap[correction.field_name] = correction.corrected_value;
      });

      await extractionAPI.submitValidation(documentId, correctionsMap);
      setSuccess(`Berhasil menyimpan ${corrections.length} koreksi. Data akan digunakan untuk melatih model.`);
      setCorrections([]);
      
      if (onValidationComplete) {
        setTimeout(() => {
          onValidationComplete();
        }, 1500); // Delay to show success message
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Gagal menyimpan validasi';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleValidateAllCorrect = async () => {
    if (!documentId) {
      setError('Document ID tidak ditemukan');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      // Submit with empty corrections to indicate all data is correct
      await extractionAPI.submitValidation(documentId, {});
      setSuccess('Berhasil memvalidasi data. Semua data ekstraksi sudah benar dan akan digunakan untuk melatih model.');
      
      if (onValidationComplete) {
        setTimeout(() => {
          onValidationComplete();
        }, 1500); // Delay to show success message
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Gagal menyimpan validasi';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  if (!extractionResults || !extractionResults.extracted_data) {
    return (
      <Card>
        <CardContent className="p-6">
          <Alert>
            <AlertCircle className="w-4 h-4" />
            <AlertDescription>
              Belum ada hasil ekstraksi. Silakan ekstraksi dokumen terlebih dahulu.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  const fields = Object.keys(extractionResults.extracted_data || {});

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CheckCircle2 className="w-6 h-6" />
          Validasi & Koreksi Data
        </CardTitle>
        <CardDescription>
          Periksa dan koreksi data yang diekstraksi. Koreksi Anda akan digunakan untuk meningkatkan akurasi model.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="form" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="form">Form Validasi</TabsTrigger>
            <TabsTrigger value="history">
              Riwayat Koreksi ({corrections.length > 0 ? `${corrections.length} baru` : feedbackHistory.length})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="form" className="space-y-4 mt-4">
            {/* Conflict Summary */}
            {/* {extractionResults.conflicts && Object.keys(extractionResults.conflicts).length > 0 && (
              <ConflictSummary conflicts={extractionResults.conflicts} />
            )} */}
            
            {/* Individual Conflicts */}
            {/* {extractionResults.conflicts && Object.entries(extractionResults.conflicts).map(([fieldName, conflict]) => {
              // Skip if dismissed
              if (dismissedConflicts.has(fieldName)) {
                return null;
              }
              
              return (
                <ConflictResolution
                  key={`conflict-${fieldName}`}
                  fieldName={fieldName}
                  conflict={conflict}
                  currentValue={formData[fieldName] || ''}
                  onResolve={handleConflictResolve}
                  onDismiss={handleConflictDismiss}
                />
              );
            })} */}
            
            <form onSubmit={handleSubmit} className="space-y-4">
              {fields.map((fieldName) => {
                const confidence = extractionResults.confidence_scores?.[fieldName] || 0;
                const method = extractionResults.extraction_methods?.[fieldName] || 
                              'unknown';
                const isModified = corrections.some(c => c.field_name === fieldName);

                return (
                  <div key={fieldName} className="space-y-2 p-4 border rounded-lg">
                    <div className="flex items-center justify-between">
                      <Label htmlFor={fieldName} className="text-base font-semibold">
                        {fieldName.replace(/_/g, ' ').toUpperCase()}
                      </Label>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="text-xs">
                          {method}
                        </Badge>
                        <Badge className={`text-xs ${getConfidenceBadgeColor(confidence)}`}>
                          {(confidence * 100).toFixed(0)}%
                        </Badge>
                        {isModified && (
                          <Badge variant="secondary" className="text-xs">
                            Dikoreksi
                          </Badge>
                        )}
                      </div>
                    </div>
                    <Input
                      id={fieldName}
                      value={formData[fieldName] || ''}
                      onChange={(e) => handleFieldChange(fieldName, e.target.value)}
                      className={isModified ? 'border-yellow-500 bg-yellow-50' : ''}
                    />
                    {confidence < 0.5 && (
                      <p className="text-xs text-destructive flex items-center gap-1">
                        <AlertCircle className="w-3 h-3" />
                        Confidence rendah - mohon periksa dengan teliti
                      </p>
                    )}
                  </div>
                );
              })}

              {error && (
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              {success && (
                <Alert>
                  <CheckCircle2 className="w-4 h-4" />
                  <AlertDescription>{success}</AlertDescription>
                </Alert>
              )}

              {/* Conditional Button: Show 'Validasi Semua Benar' when no corrections, otherwise 'Simpan Koreksi' */}
              {corrections.length === 0 && feedbackHistory.length === 0 ? (
                <Button
                  type="button"
                  onClick={handleValidateAllCorrect}
                  disabled={loading}
                  className="w-full bg-green-600 hover:bg-green-700"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Memvalidasi...
                    </>
                  ) : (
                    <>
                      <ThumbsUp className="w-4 h-4 mr-2" />
                      Validasi Semua Benar
                    </>
                  )}
                </Button>
              ) : (
                <Button
                  type="submit"
                  disabled={loading || corrections.length === 0}
                  className="w-full"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Menyimpan...
                    </>
                  ) : (
                    <>
                      <Save className="w-4 h-4 mr-2" />
                      Simpan Koreksi ({corrections.length})
                    </>
                  )}
                </Button>
              )}
            </form>
          </TabsContent>

          <TabsContent value="history" className="mt-4">
            <div className="space-y-4">
              {/* Current Corrections (Not Yet Saved) */}
              {corrections.length > 0 && (
                <div className="space-y-3">
                  <div className="flex items-center gap-2 pb-2 border-b">
                    <AlertCircle className="w-4 h-4 text-amber-500" />
                    <h3 className="font-semibold text-sm">Koreksi Saat Ini (Belum Disimpan)</h3>
                  </div>
                  {corrections.map((correction, index) => (
                    <div key={index} className="p-4 border-2 border-amber-200 rounded-lg bg-amber-50">
                      <p className="font-semibold text-sm mb-2">
                        {correction.field_name.replace(/_/g, ' ').toUpperCase()}
                      </p>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <p className="text-muted-foreground">Nilai Asli:</p>
                          <p className="font-mono text-destructive line-through">
                            {correction.original_value || '(kosong)'}
                          </p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">Nilai Koreksi:</p>
                          <p className="font-mono text-green-600 font-semibold">
                            {correction.corrected_value}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Past Feedback History (From DB) */}
              {feedbackHistory.length > 0 && (
                <div className="space-y-3">
                  <div className="flex items-center gap-2 pb-2 border-b">
                    <CheckCircle2 className="w-4 h-4 text-green-600" />
                    <h3 className="font-semibold text-sm">Riwayat Koreksi Tersimpan</h3>
                  </div>
                  {(() => {
                    // Group by field_name
                    const groupedFeedback = feedbackHistory.reduce((acc, feedback) => {
                      if (!acc[feedback.field_name]) {
                        acc[feedback.field_name] = [];
                      }
                      acc[feedback.field_name].push(feedback);
                      return acc;
                    }, {} as Record<string, FeedbackRecord[]>);

                    const formatDate = (dateString: string) => {
                      const date = new Date(dateString);
                      return date.toLocaleString('id-ID', {
                        day: '2-digit',
                        month: 'short',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      });
                    };

                    return Object.entries(groupedFeedback).map(([fieldName, records]) => (
                      <div key={fieldName} className="border rounded-lg p-4 space-y-3 bg-muted/50">
                        <div className="flex items-center justify-between">
                          <h4 className="font-semibold text-sm uppercase">
                            {fieldName.replace(/_/g, ' ')}
                          </h4>
                          <Badge variant={records[0].used_for_training ? "default" : "secondary"}>
                            {records[0].used_for_training ? (
                              <><CheckCircle2 className="w-3 h-3 mr-1" /> Digunakan untuk Training</>
                            ) : (
                              <><Clock className="w-3 h-3 mr-1" /> Belum Digunakan</>
                            )}
                          </Badge>
                        </div>

                        {records.map((record, index) => (
                          <div key={record.id} className="space-y-2">
                            {index > 0 && <div className="border-t pt-2" />}
                            
                            <div className="flex items-start gap-3">
                              <div className="flex-1 space-y-1">
                                {record.original_value && (
                                  <div className="flex items-center gap-2 text-sm">
                                    <span className="text-muted-foreground">Original:</span>
                                    <span className="line-through text-red-600">{record.original_value}</span>
                                  </div>
                                )}
                                
                                <div className="flex items-center gap-2 text-sm">
                                  <ArrowRight className="w-4 h-4 text-muted-foreground" />
                                  <span className="text-muted-foreground">Koreksi:</span>
                                  <span className="font-medium text-green-600">{record.corrected_value}</span>
                                </div>

                                {record.confidence_score !== null && (
                                  <div className="text-xs text-muted-foreground">
                                    Confidence: {(record.confidence_score * 100).toFixed(1)}%
                                  </div>
                                )}
                              </div>

                              <div className="text-xs text-muted-foreground text-right">
                                <div>{formatDate(record.created_at)}</div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    ));
                  })()}
                </div>
              )}

              {/* Empty State */}
              {corrections.length === 0 && feedbackHistory.length === 0 && (
                <Alert>
                  <AlertDescription>
                    Belum ada koreksi. Ubah nilai field di tab Form Validasi untuk membuat koreksi.
                  </AlertDescription>
                </Alert>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
