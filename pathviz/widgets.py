"""Small pygame UI helpers: text, button, slider."""
from __future__ import annotations

from typing import Callable, Optional, Union

import pygame

from . import theme

Color = tuple[int, int, int]
_fonts: dict[tuple[int, bool], pygame.font.Font] = {}


def font(size: int, bold: bool = False) -> pygame.font.Font:
    key = (size, bold)
    if key not in _fonts:
        _fonts[key] = pygame.font.SysFont("segoeui,arial", size, bold=bold)
    return _fonts[key]


def mix(a: Color, b: Color, t: float) -> Color:
    return (int(a[0] + (b[0] - a[0]) * t),
            int(a[1] + (b[1] - a[1]) * t),
            int(a[2] + (b[2] - a[2]) * t))


def draw_text(surface, text, pos, size=14, color=theme.TEXT, bold=False, align="left"):
    image = font(size, bold).render(text, True, color)
    rect = image.get_rect()
    if align == "right":
        rect.topright = pos
    elif align == "center":
        rect.center = pos
    else:
        rect.topleft = pos
    surface.blit(image, rect)
    return rect


class Button:
    def __init__(
        self,
        rect,
        label: Union[str, Callable[[], str]],
        on_click: Callable[[], None],
        *,
        active: Optional[Callable[[], bool]] = None,
        primary: bool = False,
    ) -> None:
        self.rect = pygame.Rect(rect)
        self.label = label
        self.on_click = on_click
        self.active = active
        self.primary = primary

    def handle(self, event) -> bool:
        if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                and self.rect.collidepoint(event.pos)):
            self.on_click()
            return True
        return False

    def draw(self, surface, mouse_pos) -> None:
        hover = self.rect.collidepoint(mouse_pos)
        selected = bool(self.active and self.active())
        if self.primary:
            bg = theme.ACCENT_HOVER if hover else theme.ACCENT
            fg = theme.ACCENT_TEXT
        else:
            bg = theme.BTN_ACTIVE if selected else (theme.BTN_HOVER if hover else theme.BTN)
            fg = theme.TEXT
        pygame.draw.rect(surface, bg, self.rect, border_radius=6)
        if selected and not self.primary:
            pygame.draw.rect(surface, theme.ACCENT, self.rect, 1, border_radius=6)
        text = self.label() if callable(self.label) else self.label
        draw_text(surface, text, self.rect.center, 14, fg,
                  bold=self.primary or selected, align="center")


class Slider:
    def __init__(self, rect, value: float = 0.5) -> None:
        self.rect = pygame.Rect(rect)
        self.value = value
        self.dragging = False

    def _set_from_x(self, x: int) -> None:
        self.value = min(max((x - self.rect.left) / self.rect.width, 0.0), 1.0)

    def handle(self, event) -> bool:
        if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                and self.rect.inflate(0, 14).collidepoint(event.pos)):
            self.dragging = True
            self._set_from_x(event.pos[0])
            return True
        if event.type == pygame.MOUSEMOTION and self.dragging:
            self._set_from_x(event.pos[0])
            return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dragging:
            self.dragging = False
            return True
        return False

    def draw(self, surface) -> None:
        cy = self.rect.centery
        track = pygame.Rect(self.rect.left, cy - 2, self.rect.width, 4)
        pygame.draw.rect(surface, theme.BTN_HOVER, track, border_radius=2)
        fill = track.copy()
        fill.width = int(self.rect.width * self.value)
        pygame.draw.rect(surface, theme.ACCENT, fill, border_radius=2)
        pygame.draw.circle(surface, theme.TEXT, (fill.right, cy), 7)
