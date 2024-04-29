// Welcome to JavaScript! This is where we can write code
// that makes our website more interactive.

// Helper function to create an element with attributes and children
function createElement(tag, attributes, ...children) {
  const element = document.createElement(tag);
  for (const [key, value] of Object.entries(attributes || {})) {
    if (key.startsWith('_') && key.endsWith('_')) {
      element.setAttribute(key.slice(1, -1), value);
    } else {
      element[key] = value;
    }
  }
  for (const child of children) {
    if (typeof child === 'string') {
      element.appendChild(document.createTextNode(child));
    } else {
      element.appendChild(child);
    }
  }
  return element;
}

// Create and append elements to the body
const unlock = () => {
  if (document.getElementById('unlockInput').value !== 'ssrousehill290424') {
    alert('Incorrect password');
    return;
  }

  const body = document.body;

  body.appendChild(createElement('h1', null, "Hi this is Ethan's pro web"));
  body.appendChild(
    document.createTextNode(
      'Hi this will be the best website ever have fun here'
    )
  );

  const sidebyside = createElement('div', { _class_: 'sidebyside' });
  body.appendChild(sidebyside);

  const gamesDiv = createElement(
    'div',
    null,
    createElement('h2', null, 'games'),
    createElement(
      'ul',
      null,
      createElement('li', null, 'Tall man run'),
      createElement('li', null, 'Minecraft'),
      createElement('li', null, 'Sky whale')
    )
  );
  sidebyside.appendChild(gamesDiv);

  const imagesDiv = createElement(
    'div',
    null,
    createElement('img', {
      _src_:
        'https://static.wikia.nocookie.net/gameshakers/images/a/a2/Output-onlinepngtools.png',
    }),
    createElement('img', {
      _style_: 'width: 150px',
      _src_: 'https://www.webwise.ie/wp-content/uploads/2018/04/Fortnite.jpg',
    }),
    createElement('img', {
      _style_: 'width: 150px',
      _src_:
        'https://preview.redd.it/peely-buff-puff-v0-nc4lrxxqkc2b1.png?auto=webp&s=25a2d84d83914497953bb3334ac8ab9933c6e4d0',
    }),
    document.createElement('br'),
    createElement('iframe', {
      _width_: '560',
      _height_: '315',
      _src_: 'https://www.youtube.com/embed/msSc7Mv0QHY?si=VCUwt5QWAAN9Rn6e',
      _title_: 'YouTube video player',
      _frameborder_: '0',
      _allow_:
        'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share',
      _referrerpolicy_: 'strict-origin-when-cross-origin',
      _allowfullscreen_: true,
    })
  );
  sidebyside.appendChild(imagesDiv);

  body.appendChild(createElement('h2', null, 'See more'));
  body.appendChild(createElement('h2', null, 'videos'));
  body.appendChild(
    createElement(
      'a',
      {
        _href_:
          'https://www.youtube.com/results?search_query=cheats+on+fortnite+2024',
      },
      'cheating in fortnite'
    )
  );
  body.appendChild(document.createElement('br'));
  body.appendChild(
    createElement(
      'a',
      {
        _href_:
          'https://www.youtube.com/results?search_query=how+to+get+free+skins+in+fortnite+chapter+5+season+2',
      },
      'get free skins in fortnite'
    )
  );
  body.appendChild(document.createElement('br'));
  body.appendChild(
    createElement(
      'a',
      {
        _href_:
          'https://www.youtube.com/results?search_query=fortnite+live+event',
      },
      'fortnite live events'
    )
  );
  body.appendChild(
    createElement('h1', { _class_: 'centred' }, 'HOPE YOU HAVE FUN HERE !!!')
  );

  body.classList.add('styled');
  document.getElementById('unlockSection').classList.add('styled');
};

document.getElementById('unlockButton').addEventListener('click', unlock);
