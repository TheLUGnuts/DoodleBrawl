/* This component shows the top few fighters, including their stats and images. */

import { useState, useEffect, useRef } from 'react';
import { socket, useLocalhost } from '../socket.js';
import { Button, CloseButton, Dialog, Portal, Text } from "@chakra-ui/react"

import './LeaderboardModal.css'


export default function LeaderboardModal({ isOpen, setIsOpen }) {
  return (
    <Dialog.Root
        role="alertdialog"
        open={isOpen}
        size="lg"
        onOpenChange={(e) => setIsOpen(e.open)}
      >
        <Portal>
          <Dialog.Backdrop bg="gray.700/50" />
          <Dialog.Positioner>
            <Dialog.Content>
              <Dialog.CloseTrigger asChild>
                <CloseButton color="bg" />
              </Dialog.CloseTrigger>
              <Dialog.Header>
                <Dialog.Title>Leaderboard</Dialog.Title>
              </Dialog.Header>
              <Dialog.Body>
                <Text color="fg">
                  Are you sure you want to delete this item? This action cannot
                  be undone.
                </Text>
              </Dialog.Body>
              <Dialog.Footer>
                {/* Empty, could be filled later */}
              </Dialog.Footer>
            </Dialog.Content>
          </Dialog.Positioner>
        </Portal>
      </Dialog.Root>

  )
}
