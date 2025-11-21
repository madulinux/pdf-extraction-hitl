'use client';

import React, { useState } from 'react';
import { FieldConflict } from '@/lib/types/extraction.types';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Badge } from '@/components/ui/badge';
import { 
  AlertTriangle, 
  Info, 
  AlertCircle,
  CheckCircle2
} from 'lucide-react';

interface ConflictResolutionProps {
  fieldName: string;
  conflict: FieldConflict;
  currentValue: string;
  onResolve: (fieldName: string, selectedValue: string) => void;
  onDismiss?: (fieldName: string) => void;
}

export function ConflictResolution({
  fieldName,
  conflict,
  currentValue,
  onResolve,
  onDismiss
}: ConflictResolutionProps) {
  const [selectedValue, setSelectedValue] = useState<string>(currentValue);
  const [customValue, setCustomValue] = useState<string>('');
  const [useCustom, setUseCustom] = useState(false);

  const handleResolve = () => {
    const finalValue = useCustom ? customValue : selectedValue;
    onResolve(fieldName, finalValue);
  };

  const getAlertVariant = () => {
    if (conflict.level === 'major') return 'destructive';
    if (conflict.level === 'moderate') return 'default';
    return 'default';
  };

  const getIcon = () => {
    if (conflict.level === 'major') return <AlertCircle className="h-5 w-5" />;
    if (conflict.level === 'moderate') return <AlertTriangle className="h-5 w-5" />;
    return <Info className="h-5 w-5" />;
  };

  const getTitle = () => {
    if (conflict.auto_resolved) {
      return '✓ Auto-Resolved Conflict';
    }
    if (conflict.level === 'major') {
      return '🚨 Major Conflict Detected';
    }
    if (conflict.level === 'moderate') {
      return '⚠️ Moderate Conflict Detected';
    }
    return 'ℹ️ Minor Variation Detected';
  };

  const getSimilarityBadge = () => {
    const percentage = Math.round(conflict.similarity * 100);
    let variant: 'default' | 'secondary' | 'destructive' = 'default';
    
    if (percentage >= 80) variant = 'default';
    else if (percentage >= 50) variant = 'secondary';
    else variant = 'destructive';

    return (
      <Badge variant={variant} className="ml-2">
        {percentage}% similar
      </Badge>
    );
  };

  return (
    <Alert variant={getAlertVariant()} className="mb-4">
      <div className="flex items-start gap-3">
        {getIcon()}
        <div className="flex-1">
          <AlertTitle className="flex items-center">
            {getTitle()}
            {getSimilarityBadge()}
          </AlertTitle>
          
          <AlertDescription className="mt-3 space-y-4">
            {/* Description */}
            <p className="text-sm">
              The field <strong>&ldquo;{fieldName}&rdquo;</strong> has different values across the document:
            </p>

            {/* Auto-resolved message */}
            {conflict.auto_resolved && (
              <div className="flex items-center gap-2 p-3 bg-green-50 dark:bg-green-900/20 rounded-md">
                <CheckCircle2 className="h-4 w-4 text-green-600 dark:text-green-400" />
                <p className="text-sm text-green-700 dark:text-green-300">
                  System automatically selected the most complete value. You can change it if needed.
                </p>
              </div>
            )}

            {/* Suggestion */}
            {conflict.suggestion && (
              <p className="text-sm text-muted-foreground italic">
                💡 {conflict.suggestion}
              </p>
            )}

            {/* Value selection */}
            <div className="space-y-3">
              <Label>Select the correct value:</Label>
              
              <RadioGroup 
                value={useCustom ? 'custom' : selectedValue} 
                onValueChange={(value) => {
                  if (value === 'custom') {
                    setUseCustom(true);
                  } else {
                    setUseCustom(false);
                    setSelectedValue(value);
                  }
                }}
              >
                {conflict.all_values.map((v, idx) => (
                  <div key={idx} className="flex items-start space-x-3 p-3 border rounded-md hover:bg-accent/50 transition-colors">
                    <RadioGroupItem value={v.value} id={`${fieldName}-${idx}`} className="mt-1" />
                    <Label 
                      htmlFor={`${fieldName}-${idx}`} 
                      className="flex-1 cursor-pointer"
                    >
                      <div className="space-y-1">
                        <div className="font-medium">{v.value}</div>
                        <div className="text-xs text-muted-foreground flex flex-wrap gap-2">
                          <span>Page {v.page + 1}</span>
                          {v.label && <span>• Label: &ldquo;{v.label}&rdquo;</span>}
                          <span>• Confidence: {Math.round(v.confidence * 100)}%</span>
                          {v.method && <span>• Method: {v.method}</span>}
                        </div>
                      </div>
                    </Label>
                  </div>
                ))}

                {/* Custom value option */}
                <div className="flex items-start space-x-3 p-3 border rounded-md hover:bg-accent/50 transition-colors">
                  <RadioGroupItem value="custom" id={`${fieldName}-custom`} className="mt-1" />
                  <Label 
                    htmlFor={`${fieldName}-custom`} 
                    className="flex-1 cursor-pointer"
                  >
                    <div className="space-y-2">
                      <div className="font-medium">Enter custom value</div>
                      <Input
                        value={customValue}
                        onChange={(e) => {
                          setCustomValue(e.target.value);
                          setUseCustom(true);
                        }}
                        placeholder="Type the correct value here"
                        className="mt-1"
                        disabled={!useCustom}
                      />
                    </div>
                  </Label>
                </div>
              </RadioGroup>
            </div>

            {/* Actions */}
            <div className="flex gap-2 pt-2">
              <Button 
                onClick={handleResolve}
                disabled={useCustom && !customValue.trim()}
              >
                {conflict.requires_validation ? 'Confirm Selection' : 'Use Selected Value'}
              </Button>
              
              {onDismiss && !conflict.requires_validation && (
                <Button 
                  variant="outline" 
                  onClick={() => onDismiss(fieldName)}
                >
                  Keep Current
                </Button>
              )}
            </div>
          </AlertDescription>
        </div>
      </div>
    </Alert>
  );
}

interface ConflictSummaryProps {
  conflicts: Record<string, FieldConflict>;
}

export function ConflictSummary({ conflicts }: ConflictSummaryProps) {
  const conflictEntries = Object.entries(conflicts);
  
  if (conflictEntries.length === 0) {
    return null;
  }

  const majorCount = conflictEntries.filter(([, c]) => c.level === 'major').length;
  const moderateCount = conflictEntries.filter(([, c]) => c.level === 'moderate').length;
  const minorCount = conflictEntries.filter(([, c]) => c.level === 'minor').length;
  const requiresValidation = conflictEntries.filter(([, c]) => c.requires_validation).length;

  return (
    <Alert className="mb-6">
      <Info className="h-5 w-5" />
      <AlertTitle>Conflicts Detected</AlertTitle>
      <AlertDescription>
        <div className="mt-2 space-y-2">
          <p>
            Found {conflictEntries.length} field{conflictEntries.length > 1 ? 's' : ''} with inconsistent values:
          </p>
          <div className="flex gap-2 flex-wrap">
            {majorCount > 0 && (
              <Badge variant="destructive">
                {majorCount} major
              </Badge>
            )}
            {moderateCount > 0 && (
              <Badge variant="secondary">
                {moderateCount} moderate
              </Badge>
            )}
            {minorCount > 0 && (
              <Badge variant="default">
                {minorCount} minor
              </Badge>
            )}
          </div>
          {requiresValidation > 0 && (
            <p className="text-sm text-amber-600 dark:text-amber-400 font-medium">
              ⚠️ {requiresValidation} field{requiresValidation > 1 ? 's require' : ' requires'} your validation
            </p>
          )}
        </div>
      </AlertDescription>
    </Alert>
  );
}
