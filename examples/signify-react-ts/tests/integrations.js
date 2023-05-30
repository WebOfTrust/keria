import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';

(async () => {
    puppeteer.use(StealthPlugin());
    const browser = await puppeteer.launch({
        headless: false,
        delay: 5050,
        devtools: true,
      });
    const page = await browser.newPage();



    // await page.goto('http://localhost:5173');
    // const button = await page.$x("//button[contains(., 'Agent State')]");
    // await button[0].click();

    // await page.screenshot({ path: 'stealth.png', fullPage: true })

    // const p = await page.$x("//p[contains(., 'Client')]");
    // const text = await page.evaluate(el => el.textContent, p[0]);
    // console.log(text)

    //open modal

    await page.goto('http://localhost:5173');

    //open modal
    await page.click('.css-9b1tbl-MuiButtonBase-root-MuiButton-root')

    await page.type('input[id=combo-box-demo]', 'http://localhost:3901', {delay: 10})
    await page.keyboard.press('Enter');

    //get button with class css-qzbt6i-MuiButtonBase-root-MuiIconButton-root-MuiAutocomplete-popupIndicator and click it 
    const button = await page.waitForSelector(
        '.css-nxo287-MuiInputBase-input-MuiOutlinedInput-input'
        );
    await button.click();

    await page.type('.css-1t8l2tu-MuiInputBase-input-MuiOutlinedInput-input', '0123456789abcdefghijk',{delay: 10});

    // Wait and click on first result
    const searchResultSelector = '.css-sghohy-MuiButtonBase-root-MuiButton-root';
    await page.click(searchResultSelector);

    // page.on('console', msg => console.log('PAGE LOG:', msg.text()));

    const inner_html = await page.evaluate(() => document.querySelector('button:disabled').innerHTML);



    const Closebutton = await page.$x("//button[contains(., 'Close')]");
    await Closebutton[0].click();

    //.css-1d6w9lk-MuiButtonBase-root-MuiIconButton-root 
    const bb = await page.$x("//button[@aria-label='menu']")
    await page.waitForTimeout(1000)
    await bb[0].click();

    // await page.click('button[aria-label="menu"]')
    // await page.mouse.click(35, 35, { button: 'left' })
    debugger
    // const evala = await page.evaluate(() => {document.querySelector('button')});
    // console.log(evala)

    

    const clientRoute = await page.$x("//li[contains(., 'Client')]");
    await page.waitForTimeout(1000)
    await clientRoute[0].click();

    // const agentData = await page.$x("//div[contains(., 'Agent')]");
    // const rr = await agentData[0].evaluate((el) => document.querySelector('div').innerHTML);
    // console.log(rr)
    console.log('here')
    // const result = await page.waitForSelector('.identifiers')
    const result = await page.evaluate(() => {document.querySelector('div').innerHTML}
    );
    console.log(result)

    // await browser.close();
    console.log(inner_html)

})();