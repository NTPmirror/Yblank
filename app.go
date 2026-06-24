package main

import (
	"context"
	"ymusic/core"
)

type App struct {
	ctx    context.Context
	engine *core.YMusic
}

func NewApp() *App {
	return &App{
		engine: core.New(""),
	}
}

func (a *App) startup(ctx context.Context) {
	a.ctx = ctx
}

func (a *App) domReady(ctx context.Context) {
}

func (a *App) GetVersion() string {
	return a.engine.GetVersion()
}

func (a *App) DoSomething(input string) (string, error) {
	return a.engine.DoSomething(input)
}
