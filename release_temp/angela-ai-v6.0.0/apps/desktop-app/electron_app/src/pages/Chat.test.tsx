import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import Chat from './Chat';
import { useToast } from '../components/ui/use-toast';

// Mock the API functions that would be exposed via preload.js
// In a real Electron setup, this would be part of the global window object.
// Here, we mock the module that contains them.
jest.mock('../api/chat', () => ({
  startSession: jest.fn(),
  sendMessage: jest.fn(),
}));

// Mock the useToast hook
jest.mock('../components/ui/use-toast', () => ({
  useToast: jest.fn(),
}));

// Import the mocked functions after jest.mock has been called
const mockedStartSession = require('../api/chat').startSession;
const mockedSendMessage = require('../api/chat').sendMessage;
const mockedUseToast = require('../components/ui/use-toast').useToast;

describe('Chat Component', () => {
  let mockToast: jest.Mock;

  beforeEach(() => {
    // Reset mocks before each test
    mockedStartSession.mockClear();
    mockedSendMessage.mockClear();
    mockToast = jest.fn();
    mockedUseToast.mockReturnValue({ toast: mockToast });
  });

  test('renders initial state and starts a session', async () => {
    mockedStartSession.mockResolvedValue({
      session_id: 'session-123',
      greeting: 'Welcome to the chat!',
    });

    render(<Chat />);

    expect(screen.getByRole('heading', { name: /chat/i })).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Type your message...')).toBeInTheDocument();

    await waitFor(() => {
      expect(mockedStartSession).toHaveBeenCalledTimes(1);
    });

    await waitFor(() => {
      expect(screen.getByText(/welcome to the chat!/i)).toBeInTheDocument();
    });
  });

  test('handles session start failure', async () => {
    mockedStartSession.mockRejectedValue(new Error('Session start failed'));

    render(<Chat />);

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        variant: 'destructive',
        title: 'Failed to start session',
        description: 'Could not connect to the server. Please try again later.',
      });
    });
  });

  test('allows user to type and send a message', async () => {
    mockedStartSession.mockResolvedValue({
      session_id: 'session-123',
      greeting: 'Welcome!',
    });
    mockedSendMessage.mockResolvedValue({
      response_text: 'This is the AI response.',
    });

    render(<Chat />);
    await waitFor(() => expect(screen.getByText(/welcome!/i)).toBeInTheDocument());

    const input = screen.getByPlaceholderText('Type your message...');
    const sendButton = screen.getByRole('button', { name: /send/i });

    // Simulate user typing
    fireEvent.change(input, { target: { value: 'Hello AI' } });
    expect(input).toHaveValue('Hello AI');

    // Simulate clicking send
    fireEvent.click(sendButton);

    // Assert that the user's message appears immediately
    await waitFor(() => {
      expect(screen.getByText('Hello AI')).toBeInTheDocument();
    });

    // Assert that the input is cleared
    expect(input).toHaveValue('');

    // Assert that the API was called
    await waitFor(() => {
      expect(mockedSendMessage).toHaveBeenCalledWith('Hello AI', 'session-123');
    });

    // Assert that the AI's response appears
    await waitFor(() => {
      expect(screen.getByText(/this is the ai response./i)).toBeInTheDocument();
    });
  });

  test('handles message sending failure', async () => {
    mockedStartSession.mockResolvedValue({
      session_id: 'session-123',
      greeting: 'Welcome!',
    });
    mockedSendMessage.mockRejectedValue(new Error('AI service is down'));

    render(<Chat />);
    await waitFor(() => expect(screen.getByText(/welcome!/i)).toBeInTheDocument());

    const input = screen.getByPlaceholderText('Type your message...');
    fireEvent.change(input, { target: { value: 'A failing message' } });
    fireEvent.click(screen.getByRole('button', { name: /send/i }));

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        variant: 'destructive',
        title: 'Failed to get response from AI',
        description: 'Could not connect to the AI service. Please try again later.',
      });
    });
  });
});
