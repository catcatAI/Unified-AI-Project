import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

describe('Example Test', () => {
  test('renders a simple text', () => {
    render(<div>Hello, Frontend Dashboard!</div>);
    expect(screen.getByText('Hello, Frontend Dashboard!')).toBeInTheDocument();
  });
});
