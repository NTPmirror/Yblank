package core

import "fmt"

type YMusic struct {
	configPath string
	version    string
}

func New(configPath string) *YMusic {
	return &YMusic{
		configPath: configPath,
		version:    "0.1.0",
	}
}

func (y *YMusic) GetVersion() string {
	return y.version
}

func (y *YMusic) DoSomething(input string) (string, error) {
	result := fmt.Sprintf("Hello from Go core: %s", input)
	return result, nil
}
