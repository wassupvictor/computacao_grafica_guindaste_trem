"""Inicializacao, loop principal e autoteste da aplicacao."""

import math
import sys

import numpy as np
import pygame

from .animation import TrainState, track_position
from .scene import Scene
from .settings import (
    CARGO_WAGON_OFFSETS,
    CRATE_SOURCES,
    HEIGHT,
    STATION_DISTANCE,
    STOP_ADVANCES,
    TRACK_END_X,
    TRACK_START_X,
    TRAIN_SPEED,
    TRAVEL_LENGTH,
    WIDTH,
)


def self_test():
    start, end = track_position(0.0), track_position(TRAVEL_LENGTH)
    if not math.isclose(float(end[0] - start[0]), TRAVEL_LENGTH, abs_tol=1e-5):
        raise AssertionError("O trilho deve ser reto e atravessar a cena.")
    if not math.isclose(float(start[2]), float(end[2]), abs_tol=1e-5):
        raise AssertionError("As extremidades do trilho devem estar alinhadas.")
    if len(CARGO_WAGON_OFFSETS) != 3:
        raise AssertionError("A composicao deve ter exatamente tres vagoes de carga.")
    if len(CRATE_SOURCES) != len(CARGO_WAGON_OFFSETS):
        raise AssertionError("Deve haver uma caixa disponivel para cada vagao.")
    if not math.isclose(
            float(
                np.linalg.norm(
                    np.asarray(CRATE_SOURCES[0]) - np.asarray(CRATE_SOURCES[1])
                )
            ),
            4.0,
            abs_tol=1e-5,
    ):
        raise AssertionError("As caixas de suprimento devem ficar dos dois lados do guindaste.")
    state = TrainState()
    state.update(1.0, paused=False)
    if not math.isclose(state.total_distance, TRAIN_SPEED, abs_tol=1e-5):
        raise AssertionError("O movimento deve usar o delta de tempo.")
    old_distance = state.total_distance
    state.update(2.0, paused=True)
    if state.total_distance != old_distance:
        raise AssertionError("A animacao mudou enquanto estava pausada.")
    state = TrainState()
    state.update(STATION_DISTANCE / TRAIN_SPEED, paused=False)
    if state.stopped or state.loaded_wagons != 0:
        raise AssertionError("A locomotiva nao deve avancar antes de chegar o primeiro vagao.")
    state = TrainState()
    for stop_index, advance in enumerate(STOP_ADVANCES):
        target = STATION_DISTANCE + advance
        travel_time = (target - state.lap_distance) / TRAIN_SPEED
        state.update(travel_time, paused=False)
        if not state.stopped or not math.isclose(
                state.lap_distance, target, abs_tol=1e-5
        ):
            raise AssertionError("Cada veiculo deve parar alinhado com a estacao.")
        if state.stop_index != stop_index + 1:
            raise AssertionError("A ordem das paradas deve seguir a composicao.")
        if stop_index == 0:
            state.update(1.0, paused=True)
            if not state.stopped:
                raise AssertionError("A pausa deve manter o trem aguardando a carga.")
        state.update(1.0, paused=False)
        if not state.stopped or state.loaded_wagons != stop_index:
            raise AssertionError("O trem deve esperar o carregamento manual do vagao.")
        if not state.load_current_wagon(stop_index) or state.stopped:
            raise AssertionError("O vagao deve avancar somente apos receber a caixa.")
        expected_loaded = stop_index + 1
        if state.loaded_wagons != expected_loaded:
            raise AssertionError("O vagao deve receber a caixa antes de avancar.")
        if stop_index < len(STOP_ADVANCES) - 1:
            next_target = STATION_DISTANCE + STOP_ADVANCES[stop_index + 1]
            state.update((next_target - target) / TRAIN_SPEED, paused=False)
    if not math.isclose(
            state.lap_distance, STATION_DISTANCE + STOP_ADVANCES[-1], abs_tol=1e-5
    ):
        raise AssertionError("O ultimo vagao deve concluir sua parada na estacao.")
    if state.loaded_wagons != len(CARGO_WAGON_OFFSETS):
        raise AssertionError("Todos os tres vagoes devem receber uma caixa.")
    state.update(0.5, paused=False)
    if not math.isclose(
            state.lap_distance - (STATION_DISTANCE + STOP_ADVANCES[-1]),
            TRAIN_SPEED * 0.5,
            abs_tol=1e-5,
    ):
        raise AssertionError("O trem deve continuar apos a ultima parada.")
    time_to_end = (TRAVEL_LENGTH - state.lap_distance) / TRAIN_SPEED
    state.update(time_to_end, paused=False)
    if not state.finished or not math.isclose(
            state.lap_distance, TRAVEL_LENGTH, abs_tol=1e-5
    ):
        raise AssertionError("O trem deve encerrar a animacao no fim do trilho.")
    final_distance = state.total_distance
    state.update(0.5, paused=False)
    if state.total_distance != final_distance:
        raise AssertionError("O trem nao deve voltar a se mover depois de terminar.")
    track_length = float(TRACK_END_X - TRACK_START_X)
    print(
        f"Autoteste OK: trilho reto={track_length:.1f} unidades, "
        "vagoes aguardam carregamento manual"
    )


def toggle_fullscreen(scene, fullscreen):
    fullscreen = not fullscreen
    flags = pygame.OPENGL | pygame.DOUBLEBUF
    if fullscreen:
        flags |= pygame.FULLSCREEN
        size = (0, 0)
    else:
        size = (WIDTH, HEIGHT)
    pygame.display.set_mode(size, flags)

    updated_scene = Scene()
    updated_scene.train = scene.train
    updated_scene.camera = scene.camera
    updated_scene.crane = scene.crane
    updated_scene.paused = scene.paused
    return updated_scene, fullscreen


def main():
    if "--self-test" in sys.argv:
        self_test()
        return
    pygame.init()
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
    pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)
    pygame.display.set_caption("Trem de carga - locomotiva e tres vagoes")
    pygame.display.set_mode((WIDTH, HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF)
    try:
        scene = Scene()
        if "--smoke-test" in sys.argv:
            scene.render(WIDTH, HEIGHT)
            pygame.display.flip()
            return
        clock, running = pygame.time.Clock(), True
        camera_view_keys = {
            pygame.K_1: 0,
            pygame.K_2: 1,
            pygame.K_3: 2,
            pygame.K_4: 3,
            pygame.K_5: 4,
        }
        fullscreen = False
        while running:
            delta_time = min(clock.tick(60) / 1000.0, 0.05)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_p:
                        scene.paused = not scene.paused
                    elif event.key in camera_view_keys:
                        scene.camera.set_view(camera_view_keys[event.key])
                    elif event.key == pygame.K_SPACE:
                        scene.crane.press_space(scene.train)
                    elif event.key == pygame.K_F11:
                        scene, fullscreen = toggle_fullscreen(scene, fullscreen)
            keys = pygame.key.get_pressed()
            scene.crane.update(keys, delta_time, scene.train)
            scene.train.update(delta_time, scene.paused)
            width, height = pygame.display.get_window_size()
            scene.render(width, height)
            pygame.display.flip()
            if scene.train.finished:
                running = False
    finally:
        pygame.quit()
