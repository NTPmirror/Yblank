package mobile

import "ymusic/core"

var engine *core.YMusic

func Init(configPath string) {
	engine = core.New(configPath)
}

func GetVersion() string {
	if engine == nil {
		return "not initialized"
	}
	return engine.GetVersion()
}

func DoSomething(input string) string {
	if engine == nil {
		return "engine not initialized"
	}
	result, err := engine.DoSomething(input)
	if err != nil {
		return "error: " + err.Error()
	}
	return result
}
