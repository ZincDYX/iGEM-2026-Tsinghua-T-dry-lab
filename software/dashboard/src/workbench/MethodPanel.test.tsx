import {afterEach, expect, it} from 'vitest';
import {cleanup, render} from '@testing-library/react';
import {Formula} from './MethodPanel';
afterEach(cleanup);

it('renders original conservative LaTeX as MathML, not a front-end calculation', () => {
  const {container} = render(<Formula latex={String.raw`c_{OC}^{tot}=\Phi[x+\theta_{SH3}n_{SH3}^{eff}c_{dense}]+(1-\Phi)\frac{x}{K_{OC}}`}/>);
  expect(container.querySelector('math'), container.textContent ?? '').not.toBeNull();
  expect(container.querySelector('mfrac')).not.toBeNull();
  expect(container.querySelector('[role=alert]')).toBeNull();
});

it('formula commands cannot inject HTML or fetch external images', () => {
  const {container} = render(<Formula latex={String.raw`\includegraphics{https://not-authorized.invalid/secret.png}`}/>);
  expect(container.querySelector('img,script,iframe')).toBeNull();
  expect(container.querySelectorAll('[src]')).toHaveLength(0);
});
