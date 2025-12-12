/**
 * Regex Pattern Validator
 * Validates and sanitizes regex patterns for consistency
 */

export interface RegexValidationResult {
  isValid: boolean;
  error?: string;
  sanitized?: string;
}

/**
 * Sanitize regex pattern to plain string format (remove delimiters)
 * 
 * Converts various regex formats to plain string:
 * - JavaScript: /pattern/flags -> pattern
 * - Python raw: r'pattern' -> pattern
 * - Already plain: pattern -> pattern
 */
export function sanitizeRegexPattern(pattern: string): string {
  if (!pattern) return pattern;
  
  let sanitized = pattern.trim();
  
  // Remove JavaScript regex delimiters: /pattern/flags
  if (sanitized.startsWith('/')) {
    const lastSlash = sanitized.lastIndexOf('/');
    if (lastSlash > 0) {
      sanitized = sanitized.substring(1, lastSlash);
    }
  }
  
  // Remove Python raw string prefix: r'pattern' or r"pattern"
  if (sanitized.match(/^[rR]['"]/) && sanitized.length > 2) {
    sanitized = sanitized.substring(2, sanitized.length - 1);
  }
  
  // Remove quotes if wrapped: 'pattern' or "pattern"
  if ((sanitized.startsWith('"') && sanitized.endsWith('"')) ||
      (sanitized.startsWith("'") && sanitized.endsWith("'"))) {
    sanitized = sanitized.substring(1, sanitized.length - 1);
  }
  
  return sanitized;
}

/**
 * Validate regex pattern
 * 
 * @param pattern - Regex pattern string (can have delimiters)
 * @param sanitize - If true, remove delimiters before validation
 * @returns Validation result with sanitized pattern
 */
export function validateRegexPattern(
  pattern: string,
  sanitize: boolean = true
): RegexValidationResult {
  if (!pattern || pattern.trim() === '') {
    return {
      isValid: false,
      error: 'Pattern cannot be empty'
    };
  }
  
  // Sanitize pattern if requested
  const sanitized = sanitize ? sanitizeRegexPattern(pattern) : pattern;
  
  // Validate the sanitized pattern
  try {
    new RegExp(sanitized);
    return {
      isValid: true,
      sanitized
    };
  } catch (error) {
    return {
      isValid: false,
      error: `Invalid regex pattern: ${error instanceof Error ? error.message : 'Unknown error'}`
    };
  }
}

/**
 * Common regex patterns for quick reference
 * Patterns use capturing groups () to extract value from within text
 * Example: (\d+) will extract "27" from ": 27 Tahun"
 */
export const COMMON_PATTERNS = {
  email: '([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,})',
  phone: '(\\+?[0-9]{1,4}?[-.\\s]?\\(?[0-9]{1,3}?\\)?[-.\\s]?[0-9]{1,4}[-.\\s]?[0-9]{1,4}[-.\\s]?[0-9]{1,9})',
  date_slash: '(\\d{1,2}/\\d{1,2}/\\d{2,4})',
  date_dash: '(\\d{4}-\\d{2}-\\d{2})',
  date_dash_indonesia: '(\\d{2}-\\d{2}-\\d{4})',
  number: '(\\d+)',
  decimal: '(\\d+\\.\\d+)',
  alphanumeric: '([a-zA-Z0-9]+)',
  text: '([a-zA-Z\\s]+)',
  any: '(.+)',
};

/**
 * Get pattern description for common patterns
 */
export function getPatternDescription(pattern: string): string | null {
  const descriptions: Record<string, string> = {
    [COMMON_PATTERNS.email]: 'Email address',
    [COMMON_PATTERNS.phone]: 'Phone number',
    [COMMON_PATTERNS.date_dash_indonesia]: 'Date (DD-MM-YYYY)',
    [COMMON_PATTERNS.date_slash]: 'Date (DD/MM/YYYY or MM/DD/YYYY)',
    [COMMON_PATTERNS.date_dash]: 'Date (YYYY-MM-DD)',
    [COMMON_PATTERNS.number]: 'Integer number',
    [COMMON_PATTERNS.decimal]: 'Decimal number',
    [COMMON_PATTERNS.alphanumeric]: 'Alphanumeric only',
    [COMMON_PATTERNS.text]: 'Text only (letters and spaces)',
    [COMMON_PATTERNS.any]: 'Any text (catch-all)',
  };
  
  return descriptions[pattern] || null;
}
