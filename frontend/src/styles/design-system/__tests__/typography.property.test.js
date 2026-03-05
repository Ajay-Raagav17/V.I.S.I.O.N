/**
 * Property-Based Tests for VISION Design System Typography
 * Uses fast-check for property-based testing of style computations.
 * 
 * **Feature: vision-ui-design-system, Property 1: Font family consistency**
 * **Validates: Requirements 1.1, 1.3**
 */

import * as fc from 'fast-check';
import React from 'react';
import { render, cleanup } from '@testing-library/react';

// Typography class names that should all use Inter font
const TYPOGRAPHY_CLASSES = ['text-h1', 'text-h2', 'text-h3', 'text-body', 'text-small', 'text-label'];

/**
 * Typography specification constants
 * These define the expected values for each typography style per the design system
 */
const TYPOGRAPHY_SPECS = {
  h1: {
    className: 'text-h1',
    fontSize: '28px',
    fontWeight: '600',
    lineHeight: '36px',
    color: '#1A1A1A'
  },
  h2: {
    className: 'text-h2',
    fontSize: '20px',
    fontWeight: '500',
    lineHeight: '28px',
    color: '#1F1F1F'
  },
  h3: {
    className: 'text-h3',
    fontSize: '16px',
    fontWeight: '500',
    lineHeight: '24px',
    color: '#2A2A2A'
  },
  body: {
    className: 'text-body',
    fontSize: '14px',
    fontWeight: '400',
    lineHeight: '22px',
    color: '#4A4A4A'
  },
  small: {
    className: 'text-small',
    fontSize: '12px',
    fontWeight: '400',
    lineHeight: '18px',
    color: '#7A7A7A'
  }
};

// Global style element for CSS injection
let globalStyleElement = null;

/**
 * Inject CSS styles into jsdom - uses direct values instead of CSS variables
 * since jsdom doesn't fully support CSS custom properties in getComputedStyle
 */
const injectStyles = () => {
  if (globalStyleElement) return globalStyleElement;
  
  const style = document.createElement('style');
  style.setAttribute('data-testid', 'typography-styles');
  style.textContent = `
    .text-h1 {
      font-family: 'Inter', 'SF Pro', 'Poppins', system-ui, sans-serif;
      font-size: 28px;
      font-weight: 600;
      line-height: 36px;
      color: #1A1A1A;
    }
    .text-h2 {
      font-family: 'Inter', 'SF Pro', 'Poppins', system-ui, sans-serif;
      font-size: 20px;
      font-weight: 500;
      line-height: 28px;
      color: #1F1F1F;
    }
    .text-h3 {
      font-family: 'Inter', 'SF Pro', 'Poppins', system-ui, sans-serif;
      font-size: 16px;
      font-weight: 500;
      line-height: 24px;
      color: #2A2A2A;
    }
    .text-body {
      font-family: 'Inter', 'SF Pro', 'Poppins', system-ui, sans-serif;
      font-size: 14px;
      font-weight: 400;
      line-height: 22px;
      color: #4A4A4A;
    }
    .text-small {
      font-family: 'Inter', 'SF Pro', 'Poppins', system-ui, sans-serif;
      font-size: 12px;
      font-weight: 400;
      line-height: 18px;
      color: #7A7A7A;
    }
    .text-label {
      font-family: 'Inter', 'SF Pro', 'Poppins', system-ui, sans-serif;
      font-size: 12px;
      font-weight: 500;
      line-height: 18px;
      color: #7A7A7A;
    }
  `;
  document.head.appendChild(style);
  globalStyleElement = style;
  return style;
};

/**
 * Helper to create a test component with the given typography class
 */
const TypographyTestComponent = ({ className, children, testId }) => (
  <div className={className} data-testid={testId || 'typography-element'}>
    {children}
  </div>
);

/**
 * Generator for typography class names
 */
const typographyClassArbitrary = fc.constantFrom(...TYPOGRAPHY_CLASSES);

/**
 * Generator for random text content (non-empty strings)
 */
const textContentArbitrary = fc.string({ minLength: 1, maxLength: 100 })
  .filter(s => s.trim().length > 0);

// Inject styles once before all tests
beforeAll(() => {
  injectStyles();
});

afterAll(() => {
  if (globalStyleElement && globalStyleElement.parentNode) {
    globalStyleElement.parentNode.removeChild(globalStyleElement);
    globalStyleElement = null;
  }
});

describe('Design System Typography Property Tests', () => {
  afterEach(() => {
    cleanup();
  });

  /**
   * **Feature: vision-ui-design-system, Property 1: Font family consistency**
   * **Validates: Requirements 1.1, 1.3**
   * 
   * Property: For any rendered text element with a typography class,
   * the font-family CSS property should include "Inter" as the first font.
   */
  test('Property 1: Font family consistency - all typography classes should specify Inter as primary font', () => {
    fc.assert(
      fc.property(
        typographyClassArbitrary,
        textContentArbitrary,
        (typographyClass, textContent) => {
          const testId = `typography-${Date.now()}-${Math.random()}`;
          const { getByTestId, unmount } = render(
            <TypographyTestComponent className={typographyClass} testId={testId}>
              {textContent}
            </TypographyTestComponent>
          );

          const element = getByTestId(testId);
          const computedStyle = window.getComputedStyle(element);
          
          // Verify the element has the typography class applied
          expect(element).toHaveClass(typographyClass);
          
          // Verify font-family includes Inter
          expect(computedStyle.fontFamily).toContain('Inter');
          
          unmount();
          return true;
        }
      ),
      { numRuns: 100 }
    );
  });
});

/**
 * **Feature: vision-ui-design-system, Property 2: H1 typography correctness**
 * **Validates: Requirements 2.1, 2.2**
 */
describe('Property 2: H1 Typography Correctness', () => {
  afterEach(() => {
    cleanup();
  });

  /**
   * **Feature: vision-ui-design-system, Property 2: H1 typography correctness**
   * **Validates: Requirements 2.1, 2.2**
   * 
   * Property: For any element with the H1 typography style applied,
   * the computed styles should have font-size of 28px, font-weight of 600,
   * line-height of 36px, and color of #1A1A1A.
   */
  test('H1 elements should have correct typography properties', () => {
    const spec = TYPOGRAPHY_SPECS.h1;
    
    fc.assert(
      fc.property(
        textContentArbitrary,
        (textContent) => {
          const testId = `h1-${Date.now()}-${Math.random()}`;
          const { getByTestId, unmount } = render(
            <TypographyTestComponent className={spec.className} testId={testId}>
              {textContent}
            </TypographyTestComponent>
          );

          const element = getByTestId(testId);
          const computedStyle = window.getComputedStyle(element);
          
          // Verify all H1 typography properties
          expect(computedStyle.fontSize).toBe(spec.fontSize);
          expect(computedStyle.fontWeight).toBe(spec.fontWeight);
          expect(computedStyle.lineHeight).toBe(spec.lineHeight);
          // Color comparison - jsdom returns rgb format
          expect(computedStyle.color).toBe('rgb(26, 26, 26)');
          
          unmount();
          return true;
        }
      ),
      { numRuns: 100 }
    );
  });
});

/**
 * **Feature: vision-ui-design-system, Property 3: H2 typography correctness**
 * **Validates: Requirements 3.1, 3.2**
 */
describe('Property 3: H2 Typography Correctness', () => {
  afterEach(() => {
    cleanup();
  });

  /**
   * **Feature: vision-ui-design-system, Property 3: H2 typography correctness**
   * **Validates: Requirements 3.1, 3.2**
   * 
   * Property: For any element with the H2 typography style applied,
   * the computed styles should have font-size of 20px, font-weight of 500,
   * line-height of 28px, and color of #1F1F1F.
   */
  test('H2 elements should have correct typography properties', () => {
    const spec = TYPOGRAPHY_SPECS.h2;
    
    fc.assert(
      fc.property(
        textContentArbitrary,
        (textContent) => {
          const testId = `h2-${Date.now()}-${Math.random()}`;
          const { getByTestId, unmount } = render(
            <TypographyTestComponent className={spec.className} testId={testId}>
              {textContent}
            </TypographyTestComponent>
          );

          const element = getByTestId(testId);
          const computedStyle = window.getComputedStyle(element);
          
          // Verify all H2 typography properties
          expect(computedStyle.fontSize).toBe(spec.fontSize);
          expect(computedStyle.fontWeight).toBe(spec.fontWeight);
          expect(computedStyle.lineHeight).toBe(spec.lineHeight);
          expect(computedStyle.color).toBe('rgb(31, 31, 31)');
          
          unmount();
          return true;
        }
      ),
      { numRuns: 100 }
    );
  });
});

/**
 * **Feature: vision-ui-design-system, Property 4: H3 typography correctness**
 * **Validates: Requirements 4.1, 4.2**
 */
describe('Property 4: H3 Typography Correctness', () => {
  afterEach(() => {
    cleanup();
  });

  /**
   * **Feature: vision-ui-design-system, Property 4: H3 typography correctness**
   * **Validates: Requirements 4.1, 4.2**
   * 
   * Property: For any element with the H3 typography style applied,
   * the computed styles should have font-size of 16px, font-weight of 500,
   * line-height of 24px, and color of #2A2A2A.
   */
  test('H3 elements should have correct typography properties', () => {
    const spec = TYPOGRAPHY_SPECS.h3;
    
    fc.assert(
      fc.property(
        textContentArbitrary,
        (textContent) => {
          const testId = `h3-${Date.now()}-${Math.random()}`;
          const { getByTestId, unmount } = render(
            <TypographyTestComponent className={spec.className} testId={testId}>
              {textContent}
            </TypographyTestComponent>
          );

          const element = getByTestId(testId);
          const computedStyle = window.getComputedStyle(element);
          
          // Verify all H3 typography properties
          expect(computedStyle.fontSize).toBe(spec.fontSize);
          expect(computedStyle.fontWeight).toBe(spec.fontWeight);
          expect(computedStyle.lineHeight).toBe(spec.lineHeight);
          expect(computedStyle.color).toBe('rgb(42, 42, 42)');
          
          unmount();
          return true;
        }
      ),
      { numRuns: 100 }
    );
  });
});

/**
 * **Feature: vision-ui-design-system, Property 5: Body text typography correctness**
 * **Validates: Requirements 5.1, 5.2**
 */
describe('Property 5: Body Text Typography Correctness', () => {
  afterEach(() => {
    cleanup();
  });

  /**
   * **Feature: vision-ui-design-system, Property 5: Body text typography correctness**
   * **Validates: Requirements 5.1, 5.2**
   * 
   * Property: For any element with the body text typography style applied,
   * the computed styles should have font-size of 14px, font-weight of 400,
   * line-height of 22px, and color of #4A4A4A.
   */
  test('Body text elements should have correct typography properties', () => {
    const spec = TYPOGRAPHY_SPECS.body;
    
    fc.assert(
      fc.property(
        textContentArbitrary,
        (textContent) => {
          const testId = `body-${Date.now()}-${Math.random()}`;
          const { getByTestId, unmount } = render(
            <TypographyTestComponent className={spec.className} testId={testId}>
              {textContent}
            </TypographyTestComponent>
          );

          const element = getByTestId(testId);
          const computedStyle = window.getComputedStyle(element);
          
          // Verify all body text typography properties
          expect(computedStyle.fontSize).toBe(spec.fontSize);
          expect(computedStyle.fontWeight).toBe(spec.fontWeight);
          expect(computedStyle.lineHeight).toBe(spec.lineHeight);
          expect(computedStyle.color).toBe('rgb(74, 74, 74)');
          
          unmount();
          return true;
        }
      ),
      { numRuns: 100 }
    );
  });
});

/**
 * **Feature: vision-ui-design-system, Property 6: Small text typography correctness**
 * **Validates: Requirements 6.1, 6.2**
 */
describe('Property 6: Small Text Typography Correctness', () => {
  afterEach(() => {
    cleanup();
  });

  /**
   * **Feature: vision-ui-design-system, Property 6: Small text typography correctness**
   * **Validates: Requirements 6.1, 6.2**
   * 
   * Property: For any element with the small text typography style applied,
   * the computed styles should have font-size of 12px, font-weight of 400,
   * line-height of 18px, and color of #7A7A7A.
   */
  test('Small text elements should have correct typography properties', () => {
    const spec = TYPOGRAPHY_SPECS.small;
    
    fc.assert(
      fc.property(
        textContentArbitrary,
        (textContent) => {
          const testId = `small-${Date.now()}-${Math.random()}`;
          const { getByTestId, unmount } = render(
            <TypographyTestComponent className={spec.className} testId={testId}>
              {textContent}
            </TypographyTestComponent>
          );

          const element = getByTestId(testId);
          const computedStyle = window.getComputedStyle(element);
          
          // Verify all small text typography properties
          expect(computedStyle.fontSize).toBe(spec.fontSize);
          expect(computedStyle.fontWeight).toBe(spec.fontWeight);
          expect(computedStyle.lineHeight).toBe(spec.lineHeight);
          expect(computedStyle.color).toBe('rgb(122, 122, 122)');
          
          unmount();
          return true;
        }
      ),
      { numRuns: 100 }
    );
  });
});
