# Accessibility report: Bed & Breakfast - demo page with accessibility problems

- **URL:** http://127.0.0.1:8123/bad-page.html
- **Scanned:** 2026-11-11 14:51 UTC (3429 ms)
- **Score:** 47/100 (grade F)
- **Verdict:** Failing - serious barriers across the page.
- **Rules failed:** 9  |  **Elements affected:** 18  |  **Rules passed:** 19

## Issues by severity

| Severity | Failed rules |
| --- | --- |
| Critical | 2 |
| Serious | 3 |
| Moderate | 4 |
| Minor | 0 |

## Violations

### 1. [Critical] `button-name` - Buttons must have discernible text

Ensure buttons have discernible text

- Rule reference: https://dequeuniversity.com/rules/axe/4.14/button-name?application=axeAPI
- Tags: wcag2a, wcag412
- Affected elements: 1

  - `button`
    ```html
    <button></button>
    ```

### 2. [Critical] `image-alt` - Images must have alternative text

Ensure <img> elements have alternative text or a role of none or presentation

- Rule reference: https://dequeuniversity.com/rules/axe/4.14/image-alt?application=axeAPI
- Tags: wcag2a, wcag111
- Affected elements: 1

  - `img`
    ```html
    <img src="building.png" width="200" height="120">
    ```

### 3. [Serious] `color-contrast` - Elements must meet minimum color contrast ratio thresholds

Ensure the contrast between foreground and background colors meets WCAG 2 AA minimum contrast ratio thresholds

- Rule reference: https://dequeuniversity.com/rules/axe/4.14/color-contrast?application=axeAPI
- Tags: wcag2aa, wcag143
- Affected elements: 1

  - `.faint`
    ```html
    <p class="faint">Our cheapest room is available this weekend. Call us.</p>
    ```

### 4. [Serious] `html-has-lang` - <html> element must have a lang attribute

Ensure every HTML document has a lang attribute

- Rule reference: https://dequeuniversity.com/rules/axe/4.14/html-has-lang?application=axeAPI
- Tags: wcag2a, wcag311
- Affected elements: 1

  - `html`
    ```html
    <html>
    ```

### 5. [Serious] `link-name` - Links must have discernible text

Ensure links have discernible text

- Rule reference: https://dequeuniversity.com/rules/axe/4.14/link-name?application=axeAPI
- Tags: wcag2a, wcag244, wcag412
- Affected elements: 1

  - `a`
    ```html
    <a href="/rooms"></a>
    ```

### 6. [Moderate] `region` - All page content should be contained by landmarks

Ensure all page content is contained by landmarks

- Rule reference: https://dequeuniversity.com/rules/axe/4.14/region?application=axeAPI
- Tags: best-practice
- Affected elements: 10

  - `img`
    ```html
    <img src="building.png" width="200" height="120">
    ```

  - `h1`
    ```html
    <h1>Sunrise Guest House</h1>
    ```

  - `h4`
    ```html
    <h4>Rooms and rates</h4>
    ```

  - `.faint`
    ```html
    <p class="faint">Our cheapest room is available this weekend. Call us.</p>
    ```

  - `p:nth-child(5)`
    ```html
    <p>Read more: <a href="/rooms"></a></p>
    ```

  - `input[type="text"]`
    ```html
    <input type="text" name="email" placeholder="Email">
    ```

  - `table`
    ```html
    <table> <tbody><tr><td>Room</td><td>Price</td></tr> <tr><td>Single</td><td>1200</td></tr> <tr><td>Double</td><td>1800</td></tr> </tbody></table>
    ```

  - `div:nth-child(8)`
    ```html
    <div id="notice">Breakfast is included.</div>
    ```

  - `div:nth-child(9)`
    ```html
    <div id="notice">Checkout is at 10am.</div>
    ```

  - `.tiny`
    ```html
    <p class="tiny">Terms and conditions apply. Prices may change without notice.</p>
    ```

### 7. [Moderate] `heading-order` - Heading levels should only increase by one

Ensure the order of headings is semantically correct

- Rule reference: https://dequeuniversity.com/rules/axe/4.14/heading-order?application=axeAPI
- Tags: best-practice
- Affected elements: 1

  - `h4`
    ```html
    <h4>Rooms and rates</h4>
    ```

### 8. [Moderate] `landmark-one-main` - Document should have one main landmark

Ensure the document has a main landmark

- Rule reference: https://dequeuniversity.com/rules/axe/4.14/landmark-one-main?application=axeAPI
- Tags: best-practice
- Affected elements: 1

  - `html`
    ```html
    <html>
    ```

### 9. [Moderate] `meta-viewport` - Zooming and scaling must not be disabled

Ensure <meta name="viewport"> does not disable text scaling and zooming

- Rule reference: https://dequeuniversity.com/rules/axe/4.14/meta-viewport?application=axeAPI
- Tags: wcag2aa, wcag144
- Affected elements: 1

  - `meta[name="viewport"]`
    ```html
    <meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
    ```

---
Automated checks catch roughly a third to a half of real accessibility problems. Always test with a keyboard and a screen reader.