import { render, screen } from '@testing-library/react';
import { ScrollArea } from './scroll-area';

describe('ScrollArea', () => {
  it('renders a scroll area', () => {
    render(<ScrollArea><div>Content</div></ScrollArea>);
    expect(screen.getByText('Content')).toBeInTheDocument();
  });
});
