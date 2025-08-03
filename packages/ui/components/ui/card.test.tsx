import { render, screen } from '@testing-library/react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './card';

describe('Card', () => {
  it('renders a card with a title and content', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Test Card</CardTitle>
          <CardDescription>This is a test card</CardDescription>
        </CardHeader>
        <CardContent>
          <p>This is the content of the test card.</p>
        </CardContent>
      </Card>
    );
    expect(screen.getByText('Test Card')).toBeInTheDocument();
    expect(screen.getByText('This is a test card')).toBeInTheDocument();
    expect(screen.getByText('This is the content of the test card.')).toBeInTheDocument();
  });
});
