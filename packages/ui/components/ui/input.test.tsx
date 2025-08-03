import { render, screen } from '@testing-library/react';
import { Input } from './input';

describe('Input', () => {
  it('renders an input', () => {
    render(<Input />);
    expect(screen.getByRole('textbox')).toBeInTheDocument();
  });
});
