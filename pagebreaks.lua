-- pagebreaks.lua
local levels = {1, 2}  -- 1=#, 2=##. Change as needed.

function Header(el)
  for _, lvl in ipairs(levels) do
    if el.level == lvl then
      return { pandoc.RawBlock('latex', '\\clearpage'), el }
    end
  end
end
