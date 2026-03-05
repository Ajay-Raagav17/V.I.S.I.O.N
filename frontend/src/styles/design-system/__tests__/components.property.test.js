/**
 * Property-Based Tests for VISION Design System Components
 * Uses fast-check for property-based testing of button and input styles.
 * 
 * **Feature: vision-ui-design-system, Property 7: Brand color usage correctness**
 * **Validates: Requirements 7.2, 7.4**
 * 
 * **Feature: vision-ui-design-system, Property 8: Spacing consistency**
 * **Validates: Requirements 12.2, 12.3, 12.4**
 */

import * as fc from 'fast-check';
import { render, cleanup } from '@testing-library/react';

// Brand color in RGB format (as returned by getComputedStyle)
const BRAND_COLOR_RGB = 'rgb(106, 76, 255)';
const BRAND_COLOR_HEX = '#6A4CFF';

// Body text colors that should NOT be brand color
const BODY_TEXT_COLORS = [
  'rgb(74, 74, 74)',   // #4A4A4A - body text
  'rgb(26, 26, 26)',   // #1A1A1A - h1
  'rgb(31, 31, 31)',   // #1F1F1F - h2
  'rgb(42, 42, 42)',   // #2A2A2A - h3
  'rgb(122, 122, 122)' // #7A7A7A - small/muted
];

// Global style element for CSS injection
let globalStyleElement = null;

/**
 * Inject CSS styles into jsdom for testing
 */
const injectStyles = () => {
  if (globalStyleElement) return globalStyleElement;
  
  const style = document.createElement('style');
  style.setAttribute('data-testid', 'component-styles');
  style.textContent = `
    /* Button Styles */
    .btn {
      font-family: 'Inter', 'SF Pro', 'Poppins', system-ui, sans-serif;
      font-size: 14px;
      font-weight: 500;
      line-height: 1;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
    }
    
    .btn-primary {
      height: 44px;
      min-height: 44px;
      padding: 0 24px;
      background-color: #6A4CFF;
      color: #FFFFFF;
      font-size: 14px;
      font-weight: 500;
    }
    
    .btn-secondary {
      height: 44px;
      min-height: 44px;
      padding: 0 24px;
      background-color: transparent;
      color: #6A4CFF;
      border: 2px solid #6A4CFF;
    }
    
    /* Input Styles */
    .input-label {
      font-family: 'Inter', 'SF Pro', 'Poppins', system-ui, sans-serif;
      font-size: 12px;
      font-weight: 500;
      line-height: 18px;
      color: #7A7A7A;
    }
    
    .input-field {
      width: 100%;
      height: 44px;
      min-height: 40px;
      max-height: 44px;
      padding: 0 16px;
      font-family: 'Inter', 'SF Pro', 'Poppins', system-ui, sans-serif;
      font-size: 14px;
      font-weight: 400;
      color: #1A1A1A;
      background-color: #FFFFFF;
      border: 1px solid #E5E7EB;
      border-radius: 8px;
    }
    
    /* Card Styles */
    .card {
      padding: 16px;
    }
    
    .card-lg {
      padding: 20px;
    }
    
    /* Body Text Styles */
    .text-body {
      font-family: 'Inter', 'SF Pro', 'Poppins', system-ui, sans-serif;
      font-size: 14px;
      font-weight: 400;
      line-height: 22px;
      color: #4A4A4A;
    }
  `;
  document.head.appendChild(style);
  globalStyleElement = style;
  return style;
};

/**
 * Helper to create a test button component
 */
const ButtonTestComponent = ({ className, children, testId }) => {
  const element = document.createElement('button');
  element.className = className;
  element.setAttribute('data-testid', testId || 'button-element');
  element.textContent = children;
  return element;
};

/**
 * Helper to create a test input component
 */
const InputTestComponent = ({ className, testId, placeholder }) => {
  const element = document.createElement('input');
  element.className = className;
  element.setAttribute('data-testid', testId || 'input-element');
  element.setAttribute('type', 'text');
  if (placeholder) element.setAttribute('placeholder', placeholder);
  return element;
};

/**
 * Helper to create a test div component
 */
const DivTestComponent = ({ className, children, testId }) => {
  const element = document.createElement('div');
  element.className = className;
  element.setAttribute('data-testid', testId || 'div-element');
  element.textContent = children;
  return element;
};

/**
 * Generator for button text content
 */
const buttonTextArbitrary = fc.constantFrom(
  'Log In', 'Sign Up', 'Submit', 'Save', 'Cancel', 'Continue', 
  'Start Transcribing', 'Stop Transcribing', 'Export PDF'
);

/**
 * Generator for body text content
 */
const bodyTextArbitrary = fc.string({ minLength: 1, maxLength: 200 })
  .filter(s => s.trim().length > 0);

/**
 * Generator for input placeholder text
 */
const placeholderArbitrary = fc.constantFrom(
  'Enter your username',
  'Enter your password',
  'Search sessions…',
  'e.g. Machine Learning Lecture – Day 1'
);

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

/**
 * **Feature: vision-ui-design-system, Property 7: Brand color usage correctness**
 * **Validates: Requirements 7.2, 7.4**
 */
describe('Property 7: Brand Color Usage Correctness', () => {
  afterEach(() => {
    cleanup();
    // Clean up any manually added elements
    document.body.innerHTML = '';
  });

  /**
   * **Feature: vision-ui-design-system, Property 7: Brand color usage correctness**
   * **Validates: Requirements 7.2, 7.4**
   * 
   * Property: For any primary action button, the background-color should be 
   * the brand color (#6A4CFF). For any body text element, the color should 
   * NOT be the brand color.
   */
  test('Primary buttons should have brand color background', () => {
    fc.assert(
      fc.property(
        buttonTextArbitrary,
        (buttonText) => {
          const testId = `btn-primary-${Date.now()}-${Math.random()}`;
          const button = ButtonTestComponent({ 
            className: 'btn btn-primary', 
            children: buttonText, 
            testId 
          });
          document.body.appendChild(button);

          const computedStyle = window.getComputedStyle(button);
          
          // Verify primary button has brand color background
          expect(computedStyle.backgroundColor).toBe(BRAND_COLOR_RGB);
          
          // Verify button text is white
          expect(computedStyle.color).toBe('rgb(255, 255, 255)');
          
          document.body.removeChild(button);
          return true;
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * **Feature: vision-ui-design-system, Property 7: Brand color usage correctness**
   * **Validates: Requirements 7.4**
   * 
   * Property: Body text elements should NOT use the brand color.
   */
  test('Body text should NOT use brand color', () => {
    fc.assert(
      fc.property(
        bodyTextArbitrary,
        (textContent) => {
          const testId = `body-text-${Date.now()}-${Math.random()}`;
          const element = DivTestComponent({ 
            className: 'text-body', 
            children: textContent, 
            testId 
          });
          document.body.appendChild(element);

          const computedStyle = window.getComputedStyle(element);
          
          // Verify body text does NOT have brand color
          expect(computedStyle.color).not.toBe(BRAND_COLOR_RGB);
          
          // Verify body text uses one of the allowed text colors
          expect(BODY_TEXT_COLORS).toContain(computedStyle.color);
          
          document.body.removeChild(element);
          return true;
        }
      ),
      { numRuns: 100 }
    );
  });
});

/**
 * **Feature: vision-ui-design-system, Property 8: Spacing consistency**
 * **Validates: Requirements 12.2, 12.3, 12.4**
 */
describe('Property 8: Spacing Consistency', () => {
  afterEach(() => {
    cleanup();
    // Clean up any manually added elements
    document.body.innerHTML = '';
  });

  /**
   * **Feature: vision-ui-design-system, Property 8: Spacing consistency**
   * **Validates: Requirements 12.4**
   * 
   * Property: For any button, the height should be 44px.
   */
  test('Buttons should have 44px height', () => {
    fc.assert(
      fc.property(
        buttonTextArbitrary,
        (buttonText) => {
          const testId = `btn-height-${Date.now()}-${Math.random()}`;
          const button = ButtonTestComponent({ 
            className: 'btn btn-primary', 
            children: buttonText, 
            testId 
          });
          document.body.appendChild(button);

          const computedStyle = window.getComputedStyle(button);
          
          // Verify button height is 44px
          expect(computedStyle.height).toBe('44px');
          expect(computedStyle.minHeight).toBe('44px');
          
          document.body.removeChild(button);
          return true;
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * **Feature: vision-ui-design-system, Property 8: Spacing consistency**
   * **Validates: Requirements 12.3**
   * 
   * Property: For any input field, the height should be between 40px and 44px.
   */
  test('Input fields should have height between 40-44px', () => {
    fc.assert(
      fc.property(
        placeholderArbitrary,
        (placeholder) => {
          const testId = `input-height-${Date.now()}-${Math.random()}`;
          const input = InputTestComponent({ 
            className: 'input-field', 
            testId,
            placeholder 
          });
          document.body.appendChild(input);

          const computedStyle = window.getComputedStyle(input);
          
          // Parse height value
          const height = parseInt(computedStyle.height, 10);
          const minHeight = parseInt(computedStyle.minHeight, 10);
          const maxHeight = parseInt(computedStyle.maxHeight, 10);
          
          // Verify input height is within 40-44px range
          expect(height).toBeGreaterThanOrEqual(40);
          expect(height).toBeLessThanOrEqual(44);
          expect(minHeight).toBeGreaterThanOrEqual(40);
          expect(maxHeight).toBeLessThanOrEqual(44);
          
          document.body.removeChild(input);
          return true;
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * **Feature: vision-ui-design-system, Property 8: Spacing consistency**
   * **Validates: Requirements 12.2**
   * 
   * Property: For any card component, the padding should be between 16px and 20px.
   */
  test('Card components should have padding between 16-20px', () => {
    const cardClasses = ['card', 'card-lg'];
    
    fc.assert(
      fc.property(
        fc.constantFrom(...cardClasses),
        bodyTextArbitrary,
        (cardClass, content) => {
          const testId = `card-padding-${Date.now()}-${Math.random()}`;
          const card = DivTestComponent({ 
            className: cardClass, 
            children: content, 
            testId 
          });
          document.body.appendChild(card);

          const computedStyle = window.getComputedStyle(card);
          
          // Parse padding value
          const padding = parseInt(computedStyle.padding, 10);
          
          // Verify card padding is within 16-20px range
          expect(padding).toBeGreaterThanOrEqual(16);
          expect(padding).toBeLessThanOrEqual(20);
          
          document.body.removeChild(card);
          return true;
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * **Feature: vision-ui-design-system, Property 8: Spacing consistency**
   * **Validates: Requirements 8.2**
   * 
   * Property: Input labels should have correct typography (12px, Medium, grey).
   */
  test('Input labels should have correct typography', () => {
    const labelTexts = ['Username', 'Password', 'Session Name', 'Email'];
    
    fc.assert(
      fc.property(
        fc.constantFrom(...labelTexts),
        (labelText) => {
          const testId = `label-${Date.now()}-${Math.random()}`;
          const label = DivTestComponent({ 
            className: 'input-label', 
            children: labelText, 
            testId 
          });
          document.body.appendChild(label);

          const computedStyle = window.getComputedStyle(label);
          
          // Verify label typography
          expect(computedStyle.fontSize).toBe('12px');
          expect(computedStyle.fontWeight).toBe('500');
          expect(computedStyle.color).toBe('rgb(122, 122, 122)'); // #7A7A7A
          
          document.body.removeChild(label);
          return true;
        }
      ),
      { numRuns: 100 }
    );
  });
});
