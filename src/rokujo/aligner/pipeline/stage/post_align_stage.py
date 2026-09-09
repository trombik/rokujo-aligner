import re

from . import BaseStage
from ..pipeline_context import PipelineContext


class PostAlignStage(BaseStage):
    """
    An ad-hoc stage to fixup the aligned lines.
    """
    def process(self, ctx: PipelineContext) -> PipelineContext:
        for index, aligned_line in enumerate(ctx.aligned_lines):
            # When markdown text is "**太字**日本語", the intention is, "太字"
            # should be rendered as bold text. However, the closing "**" fails
            # the right-flanking definition in strict CommonMark, meaning the
            # syntax is indeed invalid for producing bold text.
            #
            # This results in "**太字**日本語" in target text instead of "太字
            # 日本語". The problem is the markdown generator in trafilatura,
            # which produces "**太字**日本語" from "<bold>太字</bold>日本語"
            # in a paragraph.
            #
            # The same problem happens in "__斜体__日本語" as well, but italic
            # is rarely used in Japanese.
            #
            # This is a practical fix, or a workaround, not an ideal fix.
            if ctx.target_processor.lang == "ja":
                fixed_target = re.sub(r'[*]{2,3}([^*]+)[*]{2,3}', r"\1 ",
                                      aligned_line.target)
                aligned_line.target = fixed_target
                ctx.aligned_lines[index] = aligned_line
        return ctx
