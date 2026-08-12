"""ODE 수치해 → 3D 궤적 애니메이션. (로렌츠 끌개)

원본 영상의 메인 프로젝트를 Manim CE로 포팅한 것.
scipy로 미분방정식을 풀고 → c2p로 Manim 좌표에 얹고 →
미세하게 다른 초기조건들이 발산하는 걸 보여주고 → 카메라를 돌린다.

다른 ODE로 바꾸려면 `lorenz_system`과 `AXES_RANGES`,
`INITIAL_STATE`만 교체하면 나머지는 그대로 동작한다.

렌더:
    manim -pql ode_trajectory.py LorenzAttractor      # 프리뷰
    manim -qk  ode_trajectory.py LorenzAttractor      # 4K
"""

import numpy as np
from manim import *
from scipy.integrate import solve_ivp

from scene_base import KR_FONT, PALETTE, kr, subtitle

# ------------------------------------------------------------- 계 정의

SIGMA, RHO, BETA = 10.0, 28.0, 8.0 / 3.0


def lorenz_system(t, state, sigma=SIGMA, rho=RHO, beta=BETA):
    x, y, z = state
    return [
        sigma * (y - x),
        x * (rho - z) - y,
        x * y - beta * z,
    ]


def ode_solution_points(func, state0, time, dt=0.01):
    """solve_ivp로 궤적을 풀어 (N, 3) 배열로 돌려준다.

    dt를 줄이면 곡선이 매끄러워지지만 점이 늘어 렌더가 느려진다.
    0.01이 화질/속도 균형점.
    """
    solution = solve_ivp(
        func,
        t_span=(0, time),
        y0=state0,
        t_eval=np.arange(0, time, dt),
        rtol=1e-8,
        atol=1e-10,
    )
    return solution.y.T


# 로렌츠 끌개가 실제로 차지하는 범위. 축을 데이터에 맞춰야
# 화면에 제대로 들어온다. (기본 ThreeDAxes의 [-3,3]으로는 안 보인다)
AXES_RANGES = dict(
    x_range=(-30, 30, 10),
    y_range=(-30, 30, 10),
    z_range=(0, 55, 10),
)

INITIAL_STATE = [10.0, 10.0, 10.0]
EVOLUTION_TIME = 30.0
# 궤적이 8개를 넘으면 겹쳐서 한 덩어리 색으로 뭉개진다. 5개가 상한선.
N_TRAJECTORIES = 5
EPSILON = 1e-5  # 초기조건 사이의 미세한 차이

TRAJ_COLORS = [BLUE_B, TEAL_A, YELLOW, GOLD_B, RED_C, MAROON_B, PURPLE_B, GREEN_B]


def make_axes() -> ThreeDAxes:
    axes = ThreeDAxes(
        **AXES_RANGES,
        x_length=12,
        y_length=12,
        z_length=7,
        axis_config={"stroke_opacity": 0.35, "stroke_width": 2},
    )
    # 위쪽을 비워 제목이 z축 끝과 겹치지 않게 한다
    axes.center().shift(DOWN * 0.4)
    return axes


def build_curves(axes, states, colors):
    """초기조건 리스트 → 궤적 VMobject 리스트."""
    curves = VGroup()
    for state0, color in zip(states, colors):
        points = ode_solution_points(lorenz_system, state0, EVOLUTION_TIME)
        screen_points = [axes.c2p(*p) for p in points]

        curve = VMobject()
        if len(screen_points) > 2000:
            # 점이 촘촘하면 스플라인 피팅은 느리기만 하고 육안 차이가 없다
            curve.set_points_as_corners(screen_points)
        else:
            curve.set_points_smoothly(screen_points)
        curve.set_stroke(color=color, width=1.6, opacity=0.7)
        curves.add(curve)
    return curves


# ------------------------------------------------------------- 메인 씬


class LorenzAttractor(ThreeDScene):
    """거의 같은 곳에서 출발한 궤적들이 갈라지지만, 끝내 같은 모양 안에 갇힌다."""

    def construct(self):
        axes = make_axes()

        # ① 구도 잡기 — 카메라를 먼저 세팅해야 이후 배치가 예측된다
        self.set_camera_orientation(
            phi=68 * DEGREES,
            theta=-40 * DEGREES,
            zoom=0.85,
        )
        self.add(axes)

        # ② 제목은 3D 회전을 따라 돌면 안 되므로 화면에 고정한다
        title = kr("로렌츠 끌개", size=44).to_edge(UP, buff=0.4)
        self.add_fixed_in_frame_mobjects(title)
        self.play(Write(title), run_time=1.0)

        # ③ 미세하게 다른 초기조건 N개
        states = [
            [INITIAL_STATE[0] + i * EPSILON, INITIAL_STATE[1], INITIAL_STATE[2]]
            for i in range(N_TRAJECTORIES)
        ]
        curves = build_curves(axes, states, TRAJ_COLORS)

        # ④ 궤적의 현재 끝점을 따라다니는 점
        dots = VGroup(
            *[Dot3D(radius=0.055, color=c) for c in TRAJ_COLORS[:N_TRAJECTORIES]]
        )
        for dot, curve in zip(dots, curves):
            dot.move_to(curve.get_start())

        def follow_curve_ends(group):
            for dot, curve in zip(group, curves):
                points = curve.get_points()
                if len(points):
                    dot.move_to(points[-1])

        dots.add_updater(follow_curve_ends)
        self.add(dots)

        caption = subtitle(f"초기 위치의 차이는 소수점 다섯째 자리 ({EPSILON:g})")
        self.add_fixed_in_frame_mobjects(caption)
        self.play(FadeIn(caption, shift=UP * 0.2), run_time=0.5)

        # ⑤ 카메라를 천천히 돌려서 입체감을 만든다.
        #    고정된 3D는 2D처럼 보인다. rate는 0.04~0.08이 멀미 없는 범위.
        self.begin_ambient_camera_rotation(rate=0.05)

        # ⑥ 궤적을 그린다. 시간이 흐르는 애니메이션이므로 rate_func=linear.
        #    smooth를 쓰면 끝에서 시간이 느려지는 물리적으로 틀린 그림이 된다.
        self.play(
            *[Create(c, rate_func=linear) for c in curves],
            run_time=EVOLUTION_TIME * 0.5,
        )

        dots.clear_updaters()  # 안 지우면 다음 play에서 예상 못 한 움직임이 생긴다
        self.stop_ambient_camera_rotation()

        self.play(FadeOut(caption), run_time=0.4)
        outro = subtitle("갈라지지만, 끝내 같은 모양 안에 머문다")
        self.add_fixed_in_frame_mobjects(outro)
        self.play(FadeIn(outro, shift=UP * 0.2), run_time=0.5)

        # ⑦ 마무리로 시점을 한 번 바꿔 끌개의 나비 형태를 정면에서 보여준다
        self.move_camera(phi=75 * DEGREES, theta=30 * DEGREES, run_time=4)
        self.wait(1.5)


class LorenzTail(ThreeDScene):
    """잔상 꼬리 버전 — 궤적 전체가 아니라 최근 구간만 남는다.

    화면이 선으로 가득 차는 걸 피하고 '지금 어디 있는지'를 강조할 때.
    """

    def construct(self):
        axes = make_axes()
        self.set_camera_orientation(phi=68 * DEGREES, theta=-40 * DEGREES, zoom=0.85)
        self.add(axes)

        states = [
            [INITIAL_STATE[0] + i * 0.5, INITIAL_STATE[1], INITIAL_STATE[2]]
            for i in range(3)
        ]
        colors = [PALETTE["x"], PALETTE["y"], PALETTE["z"]]
        curves = build_curves(axes, states, colors)

        # 곡선 자체는 안 보이게 두고, 점이 그 위를 달리게 한다
        for curve in curves:
            curve.set_stroke(opacity=0)
        self.add(curves)

        dots = VGroup(*[Dot3D(radius=0.06, color=c) for c in colors])
        for dot, curve in zip(dots, curves):
            dot.move_to(curve.get_start())

        # dissipating_time 뒤로 꼬리가 사라진다. None이면 영구히 남는다.
        tails = VGroup(
            *[
                TracedPath(
                    dot.get_center,
                    stroke_color=c,
                    stroke_width=3,
                    dissipating_time=1.2,
                )
                for dot, c in zip(dots, colors)
            ]
        )
        self.add(tails, dots)

        self.begin_ambient_camera_rotation(rate=0.05)
        self.play(
            *[MoveAlongPath(d, c) for d, c in zip(dots, curves)],
            rate_func=linear,
            run_time=EVOLUTION_TIME * 0.5,
        )
        self.stop_ambient_camera_rotation()
        self.wait(1.0)


class LorenzEquations(Scene):
    """수식 카드. 3D 씬 앞에 붙여 쓰는 2D 인트로.

    변수 색이 3D 씬의 궤적 색과 같아야 시청자가 연결한다.
    """

    def construct(self):
        colors = {"x": PALETTE["x"], "y": PALETTE["y"], "z": PALETTE["z"]}

        lines = VGroup(
            MathTex(r"\frac{dx}{dt}", "=", r"\sigma", "(", "y", "-", "x", ")"),
            MathTex(r"\frac{dy}{dt}", "=", "x", "(", r"\rho", "-", "z", ")", "-", "y"),
            MathTex(r"\frac{dz}{dt}", "=", "x", "y", "-", r"\beta", "z"),
        )
        for line in lines:
            for part in line:
                tex = part.get_tex_string() if hasattr(part, "get_tex_string") else ""
                if tex in colors:
                    part.set_color(colors[tex])
        lines.arrange(DOWN, buff=0.45, aligned_edge=LEFT).scale(1.1)

        self.play(LaggedStart(*[Write(l) for l in lines], lag_ratio=0.35), run_time=3)
        self.wait(1.5)

        note = kr("세 개의 식. 세 개의 변수. 그런데 예측은 불가능하다.", size=30)
        note.next_to(lines, DOWN, buff=0.8).set_color(GREY_A)
        self.play(FadeIn(note, shift=UP * 0.2))
        self.wait(2.5)
