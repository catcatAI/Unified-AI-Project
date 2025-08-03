import { render, screen } from '@testing-library/react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './dialog';

describe('Dialog', () => {
  it('renders a dialog component', () => {
    render(
      <Dialog>
        <DialogTrigger>Open</DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Dialog Title</DialogTitle>
          </DialogHeader>
          <p>Dialog content</p>
        </DialogContent>
      </Dialog>
    );
    expect(screen.getByText('Open')).toBeInTheDocument();
  });
});
